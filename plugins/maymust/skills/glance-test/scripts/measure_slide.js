// Measures what the current viewport of a rendered slide shows.
// Evaluate the whole file as one expression in the page; it returns plain JSON data.
// render_html.py uses it, and any browser tool that can run page scripts can too.
// It briefly inserts probe elements, so take the screenshot first.
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
  // Whether some of rect survives the viewport and every ancestor that clips it, starting at
  // `from` for a box positioned as `position`. Overflow other than visible clips descendants;
  // absolutely positioned boxes escape non-positioned ancestors, and fixed boxes escape all
  // but transformed ones. Scrolling on html and body is the viewport itself. A sliver of 1px
  // or less, such as screen-reader-only text, does not count.
  const survives = (rect, from, position) => {
    let left = Math.max(rect.left, 0);
    let top = Math.max(rect.top, 0);
    let right = Math.min(rect.right, vw);
    let bottom = Math.min(rect.bottom, vh);
    for (let node = from; node && node !== document.body && node !== document.documentElement;
         node = node.parentElement) {
      const style = getComputedStyle(node);
      if (position === "absolute" && style.position === "static" && style.transform === "none") continue;
      if (position === "fixed" && style.transform === "none") continue;
      if (style.overflowX !== "visible" || style.overflowY !== "visible") {
        const box = node.getBoundingClientRect();
        left = Math.max(left, box.left);
        top = Math.max(top, box.top);
        right = Math.min(right, box.right);
        bottom = Math.min(bottom, box.bottom);
      }
      position = style.position;
    }
    return right - left > 1 && bottom - top > 1;
  };
  // Font size on the presentation screen, after CSS zoom and transforms: the drawn height of a
  // 1em probe inside the element. SVG text cannot hold the probe, so use its screen transform.
  const renderedFontPx = (el) => {
    let px;
    if (el instanceof SVGGraphicsElement) {
      const matrix = el.getScreenCTM();
      px = parseFloat(getComputedStyle(el).fontSize) * (matrix ? Math.hypot(matrix.c, matrix.d) : 1);
    } else {
      // A tag no deck CSS targets, with every property reset, so only the inherited font size
      // and the ancestors' zoom and transforms decide its height.
      const probe = document.createElement("glance-probe");
      probe.style.cssText = "all: initial !important; display: inline-block !important; " +
        "width: 0 !important; height: 1em !important; font-size: inherit !important; zoom: 1 !important";
      el.appendChild(probe);
      px = probe.getBoundingClientRect().height;
      probe.remove();
    }
    return Math.round(px * 10) / 10;
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
    if (![...range.getClientRects()].some((rect) => survives(rect, el, "static"))) continue;
    chars += [...text].length;
    const font = renderedFontPx(el);
    if (minFont === null || font < minFont) minFont = font;
    if (maxFont === null || font > maxFont) {
      maxFont = font;
      maxFontText = node.textContent.trim().replace(/\s+/g, " ").slice(0, 80);
    }
  }

  // Visual units: outermost boxed elements (cards, panels, code blocks) smaller than half
  // the screen, plus list items and table rows. Items, rows, and table cells are never counted
  // as boxes, so a bordered table counts once per row. A rough count, not a rule.
  const visible = (el) => {
    const rect = el.getBoundingClientRect();
    return shown(el) && hasText(el) &&
      survives(rect, el.parentElement, getComputedStyle(el).position) ? rect : null;
  };
  const candidates = [...document.body.querySelectorAll("*")].filter((el) => {
    if (el.matches("li, tr, td, th")) return false;
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
