"""Optional: open the real page in a browser, find the proof with the same rules, and save a crop.

The crop is a plain screenshot. Where the number sits is returned as boxes ("marks"), so a page
can draw the highlight over the image with CSS and the image stays an honest copy of the source.

Needs Playwright: pip install playwright && python -m playwright install chromium
"""
import html as html_lib

from .match import prove
from .page import is_named_source

BLOCKS = "p,li,td,th,h1,h2,h3,h4,h5,h6,blockquote,figcaption,dd,dt,section,article,div,span"

# The same normalising as page.norm, so offsets found in Python point at the same characters here.
NORM_JS = r"""s => String(s || '').replace(/ /g, ' ').replace(/[‘’]/g, "'")
  .replace(/[“”]/g, '"').replace(/\s+/g, ' ').trim()"""

# Every visible block's text, tagged so the chosen one can be found again.
COLLECT_JS = r"""
(sel) => {
  const norm = %s;
  const out = [];
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (r.width < 4 || r.height < 4 || cs.visibility === 'hidden' || cs.display === 'none'
        || parseFloat(cs.opacity || '1') < 0.05) continue;
    el.setAttribute('data-receipt', String(out.length));
    out.push(norm(el.innerText));
  }
  return out;
}
""" % NORM_JS

# Scroll the block into view, hide anything fixed or sticky that could cover it, and measure the
# crop and the number's boxes inside it.
MEASURE_JS = r"""
({ index, needle, nth, maxH }) => {
  const el = document.querySelector('[data-receipt="' + index + '"]');
  for (const e of document.querySelectorAll('body *')) {
    const p = getComputedStyle(e).position;
    if ((p === 'fixed' || p === 'sticky') && !e.contains(el)) e.style.setProperty('visibility', 'hidden', 'important');
  }
  el.scrollIntoView({ block: 'center' });
  // find the nth copy of the number in the element's text nodes (innerText and the nodes differ
  // in whitespace, so count copies rather than trusting an offset)
  const nodes = [], walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let flat = '';
  while (walker.nextNode()) { const n = walker.currentNode; nodes.push([n, flat.length]); flat += n.nodeValue; }
  flat = flat.replace(/[ \s]/g, ' ').replace(/[‘’]/g, "'").replace(/[“”]/g, '"');
  let pos = -1;
  for (let k = 0, i = flat.indexOf(needle); i >= 0; i = flat.indexOf(needle, i + 1), k++) { pos = i; if (k === nth) break; }
  const marks = [];
  const box = el.getBoundingClientRect();
  if (pos >= 0) {
    const at = off => { for (let i = nodes.length - 1; i >= 0; i--) if (nodes[i][1] <= off) return [nodes[i][0], off - nodes[i][1]]; };
    const range = document.createRange();
    const [sn, so] = at(pos), [en, eo] = at(pos + needle.length);
    range.setStart(sn, Math.min(so, sn.nodeValue.length));
    range.setEnd(en, Math.min(eo, en.nodeValue.length));
    for (const r of range.getClientRects()) if (r.width > 1 && r.height > 1) marks.push(r);
  }
  const vw = document.documentElement.clientWidth, vh = window.innerHeight, pad = 22, padY = 10;
  let w = Math.max(box.width + pad * 2, Math.min(640, vw));
  let x = Math.max(0, box.left + box.width / 2 - w / 2);
  if (x + w > vw) { x = Math.max(0, vw - w); w = Math.min(w, vw); }
  let y = box.top - padY, h = box.height + padY * 2;
  if (h > maxH) { const cy = marks.length ? marks[0].top + marks[0].height / 2 : box.top + box.height / 2; y = cy - maxH / 2; h = maxH; }
  y = Math.max(0, y); h = Math.min(h, vh - y);
  return {
    clip: { x: Math.round(x), y: Math.round(y), width: Math.round(w), height: Math.round(h) },
    marks: marks.filter(r => r.top >= y && r.bottom <= y + h).map(r => ({
      x: Math.round(r.left - x - 2), y: Math.round(r.top - y - 1), w: Math.round(r.width + 4), h: Math.round(r.height + 2) })),
  };
}
"""


def capture_page(page, claim, out_path, max_height=560):
    """With a Playwright page already on the source: prove the claim and save the crop, or refuse.
    Returns {ok: True, image, width, height, marks, passage, words, url, title} or {ok: False, reason}."""
    blocks = page.evaluate(COLLECT_JS, BLOCKS)
    named = is_named_source(page.url, page.title(), claim["source"])
    r = prove(claim, blocks, named)
    if not r["found"]:
        return {"ok": False, "reason": r["reason"]}
    text, needle = r["passage"], r["matched"]
    nth = text[:r["start"]].count(needle)
    m = page.evaluate(MEASURE_JS, {"index": r["block"], "needle": needle, "nth": nth, "maxH": max_height})
    if not m["marks"]:
        return {"ok": False, "reason": "the passage was found but the number could not be located on screen"}
    page.screenshot(path=out_path, clip=m["clip"])
    return {"ok": True, "image": out_path, "width": m["clip"]["width"], "height": m["clip"]["height"],
            "marks": m["marks"], "passage": text, "words": r["words"], "url": page.url, "title": page.title()}


def capture(url, claim, out_path, timeout_ms=30000):
    """Open `url` in headless Chromium and run capture_page."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1.5)
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(1000)
            return capture_page(page, claim, out_path)
        finally:
            browser.close()


def figure_html(result, src):
    """A <figure> for a capture: the screenshot, the number marked in CSS, and a link to the page.
    The marks are percentages of the image, so they stay on the words at any width."""
    w, h = result["width"], result["height"]
    marks = "".join(
        '<span class="receipt-mark" style="left:%.2f%%;top:%.2f%%;width:%.2f%%;height:%.2f%%"></span>'
        % (k["x"] / w * 100, k["y"] / h * 100, k["w"] / w * 100, k["h"] / h * 100) for k in result["marks"])
    esc = html_lib.escape
    return ('<figure class="receipt"><div class="receipt-shot" style="position:relative;aspect-ratio:%d/%d">'
            '<img src="%s" alt="%s" style="width:100%%;height:100%%">%s</div>'
            '<figcaption>Source: <a href="%s" rel="nofollow noopener">%s</a></figcaption></figure>'
            % (w, h, esc(src, quote=True), esc("Screenshot of the source. It reads: " + result["passage"][:300], quote=True),
               marks, esc(result["url"], quote=True), esc(result["title"] or result["url"])))


RECEIPT_CSS = (".receipt-mark{position:absolute;background:rgba(255,213,0,.35);mix-blend-mode:multiply;"
               "border-bottom:2px solid #d4a800;pointer-events:none}")
