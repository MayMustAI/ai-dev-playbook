import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/render_html.py"
SPEC = importlib.util.spec_from_file_location("render_html", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CHROME = MODULE.find_chrome()


def png_size(path):
    with open(path, "rb") as file:
        return struct.unpack(">II", file.read(24)[16:24])


@unittest.skipUnless(CHROME, "Chrome is not installed")
class RenderHtmlTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def page(self, name, body, style=""):
        path = self.dir / name
        path.write_text("<!doctype html><html><head><meta charset='utf-8'><style>"
                        f"html, body {{ margin: 0; font-family: sans-serif; }} {style}"
                        f"</style></head><body>{body}</body></html>", encoding="utf-8")
        return path

    def render(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), "--out", str(self.dir / "out"),
                                 "--size", "800x450", "--wait", "0", *args],
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["slides"]

    def test_stacked_slides_are_measured_in_their_final_visible_state(self):
        deck = self.page("deck.html", """
            <section><h1>메시지 하나</h1><p class="note">작은 각주</p></section>
            <section><div class="card">하나</div><div class="card">둘</div><ul><li>가</li><li>나</li><li>다</li></ul>
              <table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></table>
              <div style="height: 0; overflow: hidden"><div class="card">접힘</div></div>
              <span style="position: absolute; width: 1px; height: 1px; overflow: hidden">스크린리더</span>
              <div style="position: relative"><div style="height: 0; overflow: hidden">
                <p style="position: absolute; top: 0; margin: 0">탈출</p></div></div></section>
            <section><div class="half"><p style="font-size: 40px">절반</p></div>
              <p class="fade">나중에 보임</p><p style="visibility: hidden">숨김</p></section>
            <section><svg width="200" height="100" viewBox="0 0 800 400"><text y="60" font-size="40">도표</text></svg>
              <div style="zoom: 1.5"><p style="font-size: 20px">확대</p></div></section>""", """
            section { height: 100vh; overflow: hidden; }
            h1 { font-size: 72px; } .note { font-size: 12px; line-height: 1.2; } .card { background: #eee; }
            td { border: 1px solid #999; }
            span { font-size: 12px; } h1 * { font-size: 8px !important; max-height: 2px !important; zoom: 3 !important; }
            .half { transform: scale(0.5); transform-origin: top left; }
            .fade { font-size: 24px; opacity: 0; animation: fade 30s forwards; }
            @keyframes fade { to { opacity: 1; } }""")
        slides = self.render("--selector", "section", str(deck))

        self.assertEqual([png_size(slide["image"]) for slide in slides], [(800, 450)] * 4)
        title, cards, final, scaled = (slide["metrics"] for slide in slides)
        # A fractional line height must not change the measured 12px, and deck CSS aimed at spans
        # or at everything inside the title must not change the measured 72px.
        self.assertEqual((title["chars"], title["min_font_px"], title["max_font_px"], title["max_font_text"]),
                         (9, 12, 72, "메시지 하나"))
        # Bordered table cells count once per row. Text and cards clipped away (a collapsed panel,
        # screen-reader-only text) are not counted; an absolute box escaping a clipping wrapper
        # that is not its containing block is.
        self.assertEqual((cards["chars"], cards["boxes"], cards["items"], cards["units"]), (12, 2, 5, 7))
        # The 40px text is drawn at half size, the faded-in line counts, the hidden one does not.
        self.assertEqual((final["chars"], final["min_font_px"], final["max_font_px"]), (7, 20, 24))
        # SVG text drawn at a quarter of 40px, and 20px text under CSS zoom 1.5.
        self.assertEqual((scaled["chars"], scaled["min_font_px"], scaled["max_font_px"]), (4, 10, 30))

    def test_show_switches_decks_that_display_one_slide_at_a_time(self):
        deck = self.page("deck.html", """
            <div class="slide active">첫째</div><div class="slide">둘째</div>
            <script>function go(i) { document.querySelectorAll(".slide")
              .forEach((slide, j) => slide.classList.toggle("active", i === j)); }</script>""",
            ".slide { display: none; font-size: 48px; } .slide.active { display: block; }")
        slides = self.render("--selector", ".slide", "--show", "go(i);", str(deck))
        self.assertEqual([slide["metrics"]["max_font_text"] for slide in slides], ["첫째", "둘째"])

    def test_each_target_is_one_slide_and_fragment_changes_reload_the_deck(self):
        deck = self.page("deck.html", "<p id='n'></p><script>"
                         "document.getElementById('n').textContent = '장 ' + location.hash.slice(1);</script>")
        slides = self.render(f"{deck}#1", f"{deck}#2")
        self.assertEqual([slide["metrics"]["max_font_text"] for slide in slides], ["장 1", "장 2"])
        self.assertEqual([Path(slide["image"]).name for slide in slides], ["slide-01.png", "slide-02.png"])

    def test_missing_file_is_reported(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--out", str(self.dir / "out"),
                                 str(self.dir / "missing.html")], capture_output=True, text=True, timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no such file", result.stderr)


if __name__ == "__main__":
    unittest.main()
