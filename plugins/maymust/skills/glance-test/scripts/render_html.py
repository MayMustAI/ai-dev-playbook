#!/usr/bin/env python3
"""Render HTML slides to presentation-size PNGs and measure what each one shows.

Drives headless Chrome over the DevTools pipe, so it needs only Python 3 and Chrome
on macOS or Linux. Slides are either separate targets (files, URLs, or a deck path
with a fragment such as deck.html#3), or, with --selector, elements of one page that
--show brings on screen. Animations are finished before each screenshot, so images
show the final state. Prints JSON with each image path and the measure_slide.js metrics.
"""

import argparse
import base64
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]
DEFAULT_SHOW = 'el.scrollIntoView({block: "start", inline: "start", behavior: "instant"});'
SHOW = """(async () => {{
  const i = {index};
  const el = document.querySelectorAll({selector})[i];
  {show}
}})()"""
SETTLE = """(async () => {
  await document.fonts.ready;
  for (const animation of document.getAnimations()) {
    try { animation.finish(); } catch (error) { animation.pause(); }
  }
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
})()"""


def find_chrome(explicit=None):
    candidates = [explicit] if explicit else [os.environ.get("CHROME_PATH"), *CHROME_CANDIDATES]
    for candidate in filter(None, candidates):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def parse_size(text):
    try:
        width, height = (int(part) for part in text.lower().split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError("size must look like 1600x900") from None
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("size must be positive")
    return width, height


def to_url(target):
    if urlsplit(target).scheme in {"http", "https", "file", "data", "about"}:
        return target
    path, mark, fragment = target.partition("#")
    file = Path(path).expanduser().resolve()
    if not file.is_file():
        raise SystemExit(f"error: no such file: {path}")
    return file.as_uri() + mark + fragment


class DevTools:
    """Minimal Chrome DevTools Protocol client over --remote-debugging-pipe."""

    def __init__(self, chrome, timeout):
        self.timeout = timeout
        self.profile = tempfile.mkdtemp(prefix="glance-test-chrome-")
        to_chrome, self.writer = os.pipe()
        self.reader, from_chrome = os.pipe()

        def wire_pipe():
            # Chrome reads commands from fd 3 and writes replies to fd 4.
            read_end, write_end = os.dup(to_chrome), os.dup(from_chrome)
            os.dup2(read_end, 3)
            os.dup2(write_end, 4)
            os.set_inheritable(3, True)
            os.set_inheritable(4, True)

        args = [chrome, "--headless=new", "--remote-debugging-pipe", f"--user-data-dir={self.profile}",
                "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "--mute-audio",
                "--allow-file-access-from-files"]
        if os.geteuid() == 0:
            args.append("--no-sandbox")
        self.process = subprocess.Popen(args + ["about:blank"], stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        close_fds=False, preexec_fn=wire_pipe)
        os.close(to_chrome)
        os.close(from_chrome)
        self.next_id = 0
        self.buffer = b""
        self.events = []
        self.session = None

    def _read_message(self, deadline):
        while b"\0" not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.reader], [], [], remaining)[0]:
                raise SystemExit("error: Chrome did not respond in time")
            chunk = os.read(self.reader, 1 << 16)
            if not chunk:
                raise SystemExit("error: Chrome closed the DevTools pipe")
            self.buffer += chunk
        message, _, self.buffer = self.buffer.partition(b"\0")
        return json.loads(message)

    def send(self, method, params=None, session=None):
        self.next_id += 1
        payload = {"id": self.next_id, "method": method, "params": params or {}}
        if session:
            payload["sessionId"] = session
        data = json.dumps(payload).encode() + b"\0"
        while data:
            data = data[os.write(self.writer, data):]
        deadline = time.monotonic() + self.timeout
        while True:
            message = self._read_message(deadline)
            if message.get("id") == self.next_id:
                if "error" in message:
                    raise SystemExit(f"error: {method}: {message['error'].get('message')}")
                return message.get("result", {})
            self.events.append(message)

    def wait_event(self, method):
        deadline = time.monotonic() + self.timeout
        while True:
            for index, event in enumerate(self.events):
                if event.get("method") == method and event.get("sessionId") == self.session:
                    return self.events.pop(index)
            self.events.append(self._read_message(deadline))

    def open_page(self, width, height):
        target = self.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        self.session = self.send("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
        self.send("Page.enable", session=self.session)
        self.send("Emulation.setDeviceMetricsOverride",
                  {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False}, self.session)

    def load(self, url):
        # Leave the current document first, so a fragment-only change also reloads the deck.
        for address in ("about:blank", url):
            self.events.clear()
            result = self.send("Page.navigate", {"url": address}, self.session)
            if result.get("errorText"):
                raise SystemExit(f"error: cannot open {url}: {result['errorText']}")
            self.wait_event("Page.loadEventFired")

    def evaluate(self, expression):
        result = self.send("Runtime.evaluate", {"expression": expression, "awaitPromise": True,
                                                "returnByValue": True}, self.session)
        if "exceptionDetails" in result:
            details = result["exceptionDetails"]
            message = details.get("exception", {}).get("description") or details.get("text")
            raise SystemExit(f"error: page script failed: {message}")
        return result["result"].get("value")

    def screenshot(self):
        return base64.b64decode(self.send("Page.captureScreenshot", {"format": "png"}, self.session)["data"])

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        os.close(self.reader)
        os.close(self.writer)
        shutil.rmtree(self.profile, ignore_errors=True)


def slides(page, targets, urls, selector, show):
    """Bring each slide on screen in turn and yield where it came from."""
    if not selector:
        for target, url in zip(targets, urls):
            page.load(url)
            yield target
        return
    page.load(urls[0])
    count = page.evaluate(f"document.querySelectorAll({json.dumps(selector)}).length")
    if not count:
        raise SystemExit(f"error: --selector matched no elements: {selector}")
    for index in range(count):
        page.evaluate(SHOW.format(index=index, selector=json.dumps(selector), show=show))
        yield f"{targets[0]} [{index}]"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render HTML slides to PNGs and measure each one.")
    parser.add_argument("targets", nargs="+", help="slide files or URLs in order, or one deck with --selector")
    parser.add_argument("--out", required=True, help="directory for slide-NN.png")
    parser.add_argument("--size", type=parse_size, default=(1600, 900), help="presentation size (default 1600x900)")
    parser.add_argument("--selector", help="CSS selector that matches every slide of one page")
    parser.add_argument("--show", help="JS run for each slide with i and el set; default scrolls el into view")
    parser.add_argument("--wait", type=int, default=300, help="milliseconds to wait after showing a slide")
    parser.add_argument("--timeout", type=float, default=30, help="seconds to wait for each Chrome reply")
    parser.add_argument("--chrome", help="Chrome or Chromium binary")
    args = parser.parse_args(argv)
    if args.selector and len(args.targets) != 1:
        parser.error("--selector takes exactly one deck")
    if args.show and not args.selector:
        parser.error("--show needs --selector")

    chrome = find_chrome(args.chrome)
    if not chrome:
        raise SystemExit("error: Chrome not found; pass --chrome or set CHROME_PATH")
    urls = [to_url(target) for target in args.targets]
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    measure = (HERE / "measure_slide.js").read_text(encoding="utf-8")
    width, height = args.size

    page = DevTools(chrome, args.timeout)
    results = []
    try:
        page.open_page(width, height)
        for number, source in enumerate(slides(page, args.targets, urls, args.selector,
                                               args.show or DEFAULT_SHOW), start=1):
            time.sleep(args.wait / 1000)
            page.evaluate(SETTLE)
            metrics = page.evaluate(measure)
            image = out / f"slide-{number:02d}.png"
            image.write_bytes(page.screenshot())
            results.append({"slide": number, "source": source, "image": str(image), "metrics": metrics})
    finally:
        page.close()

    json.dump({"size": [width, height], "slides": results}, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
