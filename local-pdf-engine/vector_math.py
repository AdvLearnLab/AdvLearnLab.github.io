"""Recover LaTeX from the positioned glyphs of a vector PDF formula."""

from __future__ import annotations

import re
from statistics import median


SYMBOLS = {
    "→": r"\to", "←": r"\leftarrow", "↔": r"\leftrightarrow",
    "∈": r"\in", "∉": r"\notin", "⊂": r"\subset", "⊆": r"\subseteq",
    "⊃": r"\supset", "⊇": r"\supseteq", "∩": r"\cap", "∪": r"\cup",
    "≈": r"\approx", "≠": r"\neq", "≥": r"\geq", "≤": r"\leq",
    "∅": r"\emptyset", "∞": r"\infty", "±": r"\pm", "×": r"\times",
    "·": r"\cdot", "∑": r"\sum", "∏": r"\prod", "∫": r"\int",
    "√": r"\sqrt", "∂": r"\partial", "∇": r"\nabla",
    "∀": r"\forall", "∃": r"\exists", "¬": r"\neg", "∧": r"\land", "∨": r"\lor",
    "⇒": r"\Rightarrow", "⇔": r"\Leftrightarrow", "⊥": r"\perp", "⊤": r"\top",
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\epsilon", "θ": r"\theta", "λ": r"\lambda", "μ": r"\mu",
    "π": r"\pi", "ρ": r"\rho", "σ": r"\sigma", "τ": r"\tau",
    "φ": r"\phi", "ω": r"\omega", "′": r"\prime",
}


def _translate(text: str, roman: bool = False) -> str:
    # CMEX encodes scalable parentheses as control characters in text extraction.
    text = text.replace("\x02", "(").replace("\x03", ")")
    text = text.replace("\u00ad", "").strip()
    result = ""
    for char in text:
        mapped = SYMBOLS.get(char)
        if mapped:
            result += " " + mapped + " "
        elif char in "#$%&_{}":
            result += "\\" + char
        else:
            result += char
    result = re.sub(r"\s+", " ", result).strip()
    if roman and re.fullmatch(r"[A-Za-z][A-Za-z0-9 .-]*", result):
        return r"\mathrm{" + result.replace(" ", r"\ ") + "}"
    return result


def _span_origin_y(span: dict) -> float:
    return float(span.get("origin", (0, span["bbox"][3]))[1])


def _one_formula(spans: list[dict]) -> str:
    spans = [s for s in spans if s.get("text", "").strip(" \t\r\n") or "CMEX" in s.get("font", "")]
    if not spans:
        return ""
    sizes = [float(s.get("size", 0)) for s in spans]
    base_size = max(sizes)
    normal = [s for s in spans if float(s.get("size", 0)) >= base_size * 0.88]
    base_y = median(_span_origin_y(s) for s in normal) if normal else median(_span_origin_y(s) for s in spans)

    anchors = sorted(normal, key=lambda s: (s["bbox"][0], _span_origin_y(s)))
    scripts: dict[int, dict[str, list[dict]]] = {id(s): {"sub": [], "sup": []} for s in anchors}
    for script in (s for s in spans if s not in normal):
        x0 = script["bbox"][0]
        candidates = [a for a in anchors if a["bbox"][0] <= x0 + 0.8]
        anchor = max(candidates, key=lambda a: a["bbox"][0]) if candidates else (anchors[0] if anchors else None)
        if anchor is None:
            continue
        kind = "sup" if _span_origin_y(script) < base_y - base_size * 0.18 else "sub"
        scripts[id(anchor)][kind].append(script)

    pieces: list[str] = []
    for span in anchors:
        font = span.get("font", "")
        raw = span.get("text", "")
        roman = "Nimbus" in font and raw.strip() not in {"max", "Pr", "Sim", "s.t."}
        value = _translate(raw, roman=roman)
        if raw.strip() == "max":
            value = r"\max"
        elif raw.strip() in {"Pr", "Sim"}:
            value = "\\operatorname{" + raw.strip() + "}"
        elif raw.strip() == "s.t.":
            value = r"\mathrm{s.t.}"
        for kind in ("sub", "sup"):
            attached = sorted(scripts[id(span)][kind], key=lambda s: (s["bbox"][0], _span_origin_y(s)))
            if attached:
                body = "".join(_translate(s.get("text", ""), roman="Nimbus" in s.get("font", "")) for s in attached)
                value += ("_{" if kind == "sub" else "^{") + body + "}"
        pieces.append(value)

    latex = " ".join(p for p in pieces if p)
    latex = re.sub(r"/\s*\\in\b", r"\\notin", latex)
    latex = re.sub(r"\s+([,.;:)])", r"\1", latex)
    latex = re.sub(r"([(])\s+", r"\1", latex)
    return re.sub(r"\s+", " ", latex).strip()


def vector_formula_to_latex(block: dict) -> str:
    """Convert one detected display block, retaining rows as an aligned equation."""
    spans = [span for line in block.get("lines", []) for span in line.get("spans", [])]
    if not spans:
        return ""
    base_size = max(float(s.get("size", 0)) for s in spans)
    baseline_groups: list[list[dict]] = []
    # A new equation row has a genuinely different normal-size baseline; script rows do not.
    for span in sorted(spans, key=lambda s: (_span_origin_y(s), s["bbox"][0])):
        if float(span.get("size", 0)) < base_size * 0.88 or "CMEX" in span.get("font", ""):
            continue
        y = _span_origin_y(span)
        group = next((g for g in baseline_groups if abs(_span_origin_y(g[0]) - y) < base_size * 0.45), None)
        (group if group is not None else baseline_groups.append([]) or baseline_groups[-1]).append(span)
    if not baseline_groups:
        return ""
    rows = []
    for group in baseline_groups:
        y = median(_span_origin_y(s) for s in group)
        row_spans = []
        # Assign every glyph to its nearest equation baseline. This keeps tall
        # delimiters and super/subscripts with the row they visually belong to.
        for script in spans:
            nearest = min(baseline_groups, key=lambda g: abs(_span_origin_y(g[0]) - _span_origin_y(script)))
            if nearest is group:
                row_spans.append(script)
        row = _one_formula(row_spans)
        if row and row not in rows:
            rows.append(row)
    if len(rows) == 1:
        return rows[0]
    return r"\begin{aligned}" + r" \\ ".join(rows) + r"\end{aligned}"
