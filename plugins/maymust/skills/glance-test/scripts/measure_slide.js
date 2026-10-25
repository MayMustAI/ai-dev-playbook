// Measures what the current viewport of a rendered slide shows.
// Evaluate the whole file as one expression in the page; it returns plain JSON data.
// render_html.py uses it, and any browser tool that can run page scripts can too.
(() => {
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  const opacity = (el) => {
    let value = 1;
    for (let node = el; node; node = node.parentElement) {
      value *= parseFloat(getComputedStyle(node).opacity);
    }
    return value;
  };
  const shown = (el) => getComputedStyle(el).visibility === "visible" && opacity(el) >= 0.1;
  const onScreen = (rect) => rect.width > 0 && rect.height > 0 &&
    rect.right > 0 && rect.bottom > 0 && rect.left < vw && rect.top < vh;
  // Computed font-size times any CSS transform scale, i.e. the size on the presentation screen.
  const renderedFontPx = (el) => {
    const size = parseFloat(getComputedStyle(el).fontSize);
    const scale = el.offsetHeight > 0 ? el.getBoundingClientRect().height / el.offsetHeight : 1;
    return Math.round(size * scale * 10) / 10;
  };
  const alpha = (color) => {
    const match = color.match(/rgba?\(([^)]*)\)/);
    if (!match) return color === "transparent" ? 0 : 1;
    const parts = match[1].split(/[\s,/]+/).filter(Boolean);
    return parts.length > 3 ? parseFloat(parts[3]) : 1;
  };
  const boxed = (style) => alpha(style.backgroundColor) > 0 || style.backgroundImage !== "none" ||
    style.boxShadow !== "none" ||
    ["Top", "Right", "Bottom", "Left"].some((side) =>
      parseFloat(style[`border${side}Width`]) > 0 && alpha(style[`border${side}Color`]) > 0);
  // SVG elements have no innerText.
  const hasText = (el) => (el.innerText ?? el.textContent ?? "").replace(/\s+/g, "").length > 0;

  let chars = 0;
  let minFont = null;
  let maxFont = null;
  let maxFontText = "";
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const text = node.textContent.replace(/\s+/g, "");
    const el = node.parentElement;
    if (!text || !el || !shown(el)) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    if (![...range.getClientRects()].some(onScreen)) continue;
    chars += [...text].length;
    const font = renderedFontPx(el);
    if (minFont === null || font < minFont) minFont = font;
    if (maxFont === null || font > maxFont) {
      maxFont = font;
      maxFontText = node.textContent.trim().replace(/\s+/g, " ").slice(0, 80);
    }
  }

  // Visual units: outermost boxed elements (cards, panels, code blocks) smaller than half
  // the screen, plus list items and table rows. A rough count, not a rule.
  const visible = (el) => {
    const rect = el.getBoundingClientRect();
    return onScreen(rect) && shown(el) && hasText(el) ? rect : null;
  };
  const candidates = [...document.body.querySelectorAll("*")].filter((el) => {
    const rect = visible(el);
    return rect && rect.width * rect.height < 0.5 * vw * vh && boxed(getComputedStyle(el));
  });
  const boxes = candidates.filter((el) => !candidates.some((other) => other !== el && other.contains(el)));
  const items = [...document.body.querySelectorAll("li, tr")].filter(visible);

  return {
    chars,
    units: boxes.length + items.length,
    boxes: boxes.length,
    items: items.length,
    min_font_px: minFont,
    max_font_px: maxFont,
    max_font_text: maxFontText,
  };
})()
