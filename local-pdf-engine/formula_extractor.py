"""Formula region extraction from PDFs (PyMuPDF).

Reusable detection logic adapted from a production PDF->DOCX pipeline. It
locates mathematical formulas on each page:

  * DISPLAY formulas : centered, non-CJK, Computer-Modern/Latin-Modern math
                       font, containing math tokens (_ ^ = Greek etc.)
  * INLINE math      : math-font spans inside body text (merged into segments)
  * LABELS           : right-aligned "(1)", "(2.3)" style equation numbers

It crops each formula to a PNG (for downstream OCR) and reports an ordered
list of ``FormulaRegion`` objects plus, optionally, the ordered raw page text.

This module does NOT perform OCR — it only finds and crops formulas. The OCR
step lives in ``ocr_adapter.py``.
"""
import os
import re
import fitz  # PyMuPDF

MATH_FONT_HINTS = ("cm", "lm", "math", "symbol", "cmmi", "cmsy", "cmex", "euler", "rsfs")
CJK = lambda s: any('\u4e00' <= c <= '\u9fff' for c in s)
MATH_TOKEN = re.compile(r'[\\_^=∑∫√±×÷≤≥≈≠∈∉∂∇∞α-ωΑ-Ω]')
LABEL_PAT = re.compile(r'^\(\d+(\.\d+)?\)$')


def sanitize(s):
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', s)


def font_is_math(f):
    return any(h in (f or '').lower() for h in MATH_FONT_HINTS)


def block_text(b):
    return " ".join("".join(s["text"] for s in l["spans"]) for l in b["lines"]).strip()


def union_rect(rects):
    x0 = min(r[0] for r in rects); y0 = min(r[1] for r in rects)
    x1 = max(r[2] for r in rects); y1 = max(r[3] for r in rects)
    return (x0 - 2, y0 - 2, x1 + 2, y1 + 2)


def inside(rect, x0, y0, x1, y1):
    return not (x1 < rect[0] or x0 > rect[2] or y1 < rect[1] or y0 > rect[3])


def detect_tables(page):
    """Paired top/bottom rule lines -> table regions (skip them as formulas)."""
    W = page.rect.width
    draws = page.get_drawings()
    hlines = []
    for d in draws:
        r = d["rect"]
        if r.height < 3 and r.width > 0.45 * W:
            hlines.append((r.x0, r.y0, r.x1, r.y1))
    hlines.sort(key=lambda h: h[1])
    regions = []
    used = [False] * len(hlines)
    for j in range(len(hlines)):
        bx0, by0, bx1, by1 = hlines[j]
        if used[j]:
            continue
        best_i, best_d = -1, 1e9
        for i in range(j):
            if used[i]:
                continue
            ax0, ay0, ax1, ay1 = hlines[i]
            if abs(ax0 - bx0) < 25 and abs(ax1 - bx1) < 25 and by0 - ay0 > 12:
                d = by0 - ay0
                if d < best_d:
                    best_d, best_i = d, i
        if best_i >= 0:
            ax0, ay0, ax1, ay1 = hlines[best_i]
            used[best_i] = used[j] = True
            regions.append((min(ax0, bx0) - 3, ay0 - 3, max(ax1, bx1) + 3, by1 + 3))
    return regions


class FormulaRegion:
    """A single detected formula on a page."""
    __slots__ = ('page', 'kind', 'bbox', 'crop_path', 'label', 'context')

    def __init__(self, page, kind, bbox, crop_path=None, label=None, context=None):
        self.page = page          # 0-based page index
        self.kind = kind          # 'display' | 'inline'
        self.bbox = bbox          # (x0, y0, x1, y1) in PDF points
        self.crop_path = crop_path
        self.label = label        # e.g. "(3)" if a trailing label was detected
        self.context = context    # optional text near the formula

    def __repr__(self):
        return f"FormulaRegion(p={self.page + 1}, {self.kind}, {self.bbox}, label={self.label})"


def is_math_display(b, W):
    text = block_text(b)
    if not text or CJK(text):
        return False
    r = b["bbox"]
    if r[0] > 0.55 * W:           # right-aligned => likely a label
        return False
    centered = abs((r[0] + r[2]) / 2 - W / 2) < 0.18 * W
    if not centered:
        return False
    math_spans = [s for l in b["lines"] for s in l["spans"]
                  if font_is_math(s["font"]) and not CJK(s["text"])]
    return bool(math_spans) and bool(MATH_TOKEN.search(text))


def is_label_block(b, W):
    t = block_text(b)
    if not t or len(t) > 12:
        return False
    if not LABEL_PAT.match(t):
        return False
    r = b["bbox"]
    return r[0] > 0.45 * W


def page_text_blocks(page):
    """Return text blocks sorted in reading order for doc reconstruction."""
    d = page.get_text("dict")
    blocks = [b for b in d["blocks"] if b["type"] == 0]
    blocks.sort(key=lambda b: (round(b["bbox"][1] / 5) * 5, b["bbox"][0]))
    return blocks


def build_segments(b, page, dpi=300):
    """Split a text block into ('text', str) / ('math', fitz.Rect) segments."""
    segs = []
    for l in b["lines"]:
        for s in l["spans"]:
            txt = sanitize(s["text"])
            if not txt:
                continue
            is_math = font_is_math(s["font"]) and not CJK(txt) and MATH_TOKEN.search(txt)
            if is_math:
                rb = fitz.Rect(s["bbox"])
                if segs and segs[-1][0] == 'math':
                    old = segs[-1][1]
                    segs[-1] = ('math', fitz.Rect(min(old.x0, rb.x0), min(old.y0, rb.y0),
                                                  max(old.x1, rb.x1), max(old.y1, rb.y1)))
                else:
                    segs.append(('math', rb))
            else:
                is_cjk = CJK(txt)
                bold = bool(s["flags"] & 2)
                if (segs and segs[-1][0] == 'text' and segs[-1][1][1] == is_cjk
                        and segs[-1][1][3] == bold):
                    segs[-1] = ('text', (segs[-1][1][0] + txt, is_cjk, segs[-1][1][2], bold))
                else:
                    segs.append(('text', (txt, is_cjk, s["size"], bold)))
    return segs


class FormulaExtractor:
    """Detect and crop formula regions from a PDF."""

    def __init__(self, pdf_path, dpi=300, tmpdir=None, margin=4):
        self.pdf_path = pdf_path
        self.dpi = dpi
        self.doc = fitz.open(pdf_path)
        self.margin = margin
        if tmpdir is None:
            tmpdir = os.path.join(os.path.dirname(os.path.abspath(pdf_path)),
                                  "_formula_crops")
        self.tmpdir = tmpdir
        os.makedirs(self.tmpdir, exist_ok=True)

    def __len__(self):
        return self.doc.page_count

    def close(self):
        self.doc.close()

    def _crop(self, page, rect, name):
        clip = fitz.Rect(rect)
        zoom = self.dpi / 72.0
        pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(zoom, zoom), alpha=False)
        if pix.width == 0 or pix.height == 0:
            return None
        path = os.path.join(self.tmpdir, name)
        pix.save(path)
        return path

    def extract(self, pages=None):
        """Return an ordered list of FormulaRegion (display + inline)."""
        n = self.doc.page_count
        lo, hi = (0, n) if pages is None else pages
        regions = []
        for pi in range(lo, hi):
            page = self.doc[pi]
            W = page.rect.width
            tables = detect_tables(page)
            d = page.get_text("dict")
            # discard figure/table regions from block list
            tbs = [b for b in d["blocks"] if b["type"] == 0]
            tbs.sort(key=lambda b: (round(b["bbox"][1] / 5) * 5, b["bbox"][0]))
            i = 0
            while i < len(tbs):
                b = tbs[i]
                r = b["bbox"]
                if any(inside(t, r[0], r[1], r[2], r[3]) for t in tables):
                    i += 1
                    continue
                if is_math_display(b, W):
                    group = [b]
                    j = i + 1
                    while j < len(tbs):
                        nb = tbs[j]
                        nr = nb["bbox"]
                        if any(inside(t, nr[0], nr[1], nr[2], nr[3]) for t in tables):
                            break
                        ntext = block_text(nb)
                        if is_label_block(nb, W) or is_math_display(nb, W):
                            group.append(nb); j += 1
                        elif ntext and not CJK(ntext):
                            ms = [s for l in nb["lines"] for s in l["spans"]
                                  if font_is_math(s["font"]) and not CJK(s["text"])]
                            if ms:
                                group.append(nb); j += 1
                            else:
                                break
                        else:
                            break
                    rect = union_rect([bb["bbox"] for bb in group])
                    rect = self._extend_brackets(page, rect)
                    label = block_text(group[-1]) if len(group) > 1 and is_label_block(group[-1], W) else None
                    crop = self._crop(page, rect, f"p{pi+1}_disp_{i}.png")
                    regions.append(FormulaRegion(pi, 'display', rect, crop, label))
                    i = j
                    continue
                # inline math inside this text block
                segs = build_segments(b, page, self.dpi)
                for kind, payload in segs:
                    if kind == 'math':
                        rect = self._extend_brackets(page, tuple(payload))
                        crop = self._crop(page, rect, f"p{pi+1}_inl_{len(regions)}.png")
                        regions.append(FormulaRegion(pi, 'inline', rect, crop))
                i += 1
        return regions

    def _extend_brackets(self, page, rect):
        """Grow the crop to include tall vertical drawings (brackets) beside math."""
        rect = list(rect)
        for ddraw in page.get_drawings():
            dr = ddraw["rect"]
            if dr.width < 3 and dr.height > 18:
                if (rect[0] - 20 <= dr.x1 <= rect[0] + 8) or (rect[2] - 8 <= dr.x0 <= rect[2] + 20):
                    rect[0] = min(rect[0], dr.x0) - 2
                    rect[1] = min(rect[1], dr.y0) - 2
                    rect[2] = max(rect[2], dr.x1) + 2
                    rect[3] = max(rect[3], dr.y1) + 2
        return tuple(rect)

    def reading_order_text(self, pages=None):
        """Yield (page_index, text) for every text block, reading order."""
        n = self.doc.page_count
        lo, hi = (0, n) if pages is None else pages
        for pi in range(lo, hi):
            page = self.doc[pi]
            for b in page_text_blocks(page):
                yield pi, block_text(b)


if __name__ == '__main__':
    import sys
    pdf = sys.argv[1] if len(sys.argv) > 1 else r"D:\boshihouchuzhan\postdoc_v7.pdf"
    ex = FormulaExtractor(pdf)
    regs = ex.extract()
    disp = [r for r in regs if r.kind == 'display']
    inl = [r for r in regs if r.kind == 'inline']
    print(f"pages={len(ex)} display={len(disp)} inline={len(inl)}")
    for r in regs[:10]:
        print(" ", r)
    ex.close()
