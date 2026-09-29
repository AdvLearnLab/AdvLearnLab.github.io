"""OMML engine: convert LaTeX math strings into Word-editable equations (OMML).

This module is the core of the `pdf-formula-to-word` skill. It contains a
self-contained, dependency-light LaTeX -> OMML parser (no external services)
so that ANY valid LaTeX math string can become a real, editable Word equation.

Public API
----------
    latex_to_oMath(latex)                       -> lxml <m:oMath> element
    insert_display_equation(doc, latex)         -> centered paragraph w/ equation
    insert_inline_equation(paragraph, latex)    -> inline equation run inside a paragraph

Dependencies: lxml (required), python-docx (only for the insert_* helpers).
"""
from lxml import etree
from docx.shared import Pt  # used by the insert_* helpers (python-docx)

M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
XML = 'http://www.w3.org/XML/1998/namespace'
MATH_NSMAP = {'m': M}


# ---------------------------------------------------------------------------
# Low-level OMML builders
# ---------------------------------------------------------------------------
def _el(tag, parent=None, text=None):
    el = etree.Element(f'{{{M}}}{tag}', nsmap=MATH_NSMAP)
    if parent is not None:
        parent.append(el)
    if text is not None:
        r = etree.SubElement(el, f'{{{M}}}r')
        t = etree.SubElement(r, f'{{{M}}}t')
        t.text = text
        t.set(f'{{{XML}}}space', 'preserve')
    return el


def _mr(text, parent=None):
    r = etree.Element(f'{{{M}}}r') if parent is None else etree.SubElement(parent, f'{{{M}}}r')
    t = etree.SubElement(r, f'{{{M}}}t')
    t.text = text
    t.set(f'{{{XML}}}space', 'preserve')
    return r


def _melem(tag, children, parent=None):
    el = etree.Element(f'{{{M}}}{tag}') if parent is None else etree.SubElement(parent, f'{{{M}}}{tag}')
    for child in children:
        if isinstance(child, str):
            _mr(child, el)
        else:
            el.append(child)
    return el


def _acc(char, child_el):
    acc = etree.Element(f'{{{M}}}acc')
    accPr = etree.SubElement(acc, f'{{{M}}}accPr')
    chr_el = etree.SubElement(accPr, f'{{{M}}}chr')
    chr_el.set(f'{{{M}}}val', char)
    e = etree.SubElement(acc, f'{{{M}}}e')
    e.append(child_el)
    return acc


def _frac(num_el, den_el):
    f = etree.Element(f'{{{M}}}f')
    num = etree.SubElement(f, f'{{{M}}}num')
    num.append(num_el)
    den = etree.SubElement(f, f'{{{M}}}den')
    den.append(den_el)
    return f


def _sub(base_el, sub_text):
    ssub = etree.Element(f'{{{M}}}sSub')
    e = etree.SubElement(ssub, f'{{{M}}}e')
    e.append(base_el)
    sub = etree.SubElement(ssub, f'{{{M}}}sub')
    _mr(sub_text, sub)
    return ssub


def _sup(base_el, sup_text):
    ssup = etree.Element(f'{{{M}}}sSup')
    e = etree.SubElement(ssup, f'{{{M}}}e')
    e.append(base_el)
    sup = etree.SubElement(ssup, f'{{{M}}}sup')
    _mr(sup_text, sup)
    return ssup


def _subsup(base_el, sub_text, sup_text):
    ss = etree.Element(f'{{{M}}}sSubSup')
    e = etree.SubElement(ss, f'{{{M}}}e')
    e.append(base_el)
    s = etree.SubElement(ss, f'{{{M}}}sub')
    _mr(sub_text, s)
    s = etree.SubElement(ss, f'{{{M}}}sup')
    _mr(sup_text, s)
    return ss


def _delim(left, right, child_el):
    d = etree.Element(f'{{{M}}}d')
    dPr = etree.SubElement(d, f'{{{M}}}dPr')
    beg = etree.SubElement(dPr, f'{{{M}}}begChr')
    beg.set(f'{{{M}}}val', left)
    end = etree.SubElement(dPr, f'{{{M}}}endChr')
    end.set(f'{{{M}}}val', right)
    e = etree.SubElement(d, f'{{{M}}}e')
    e.append(child_el)
    return d


def _rad(child_el, degree=None):
    r = etree.Element(f'{{{M}}}rad')
    if degree is None:
        rPr = etree.SubElement(r, f'{{{M}}}radPr')
        etree.SubElement(rPr, f'{{{M}}}degHide').set(f'{{{M}}}val', '1')
    else:
        deg_el = etree.Element(f'{{{M}}}deg')
        _mr(degree, deg_el)
        r.append(deg_el)
    e = etree.SubElement(r, f'{{{M}}}e')
    e.append(child_el)
    return r


def _matrix(rows_data):
    m = etree.Element(f'{{{M}}}m')
    mPr = etree.SubElement(m, f'{{{M}}}mPr')
    ncols = max((len(row) for row in rows_data), default=1)
    nrows = len(rows_data)
    mcs = etree.SubElement(mPr, f'{{{M}}}mcs')
    for _ in range(ncols):
        mc = etree.SubElement(mcs, f'{{{M}}}mc')
        mcPr = etree.SubElement(mc, f'{{{M}}}mcPr')
        count = etree.SubElement(mcPr, f'{{{M}}}count')
        count.set(f'{{{M}}}val', str(ncols))
    for row in rows_data:
        mr_el = etree.SubElement(m, f'{{{M}}}mr')
        for cell in row:
            e_el = etree.SubElement(mr_el, f'{{{M}}}e')
            if isinstance(cell, str):
                _mr(cell, e_el)
            else:
                e_el.append(cell)
    return m


# ---------------------------------------------------------------------------
# Symbol maps
# ---------------------------------------------------------------------------
GREEK = {
    'alpha': '\u03b1', 'beta': '\u03b2', 'gamma': '\u03b3', 'delta': '\u03b4',
    'epsilon': '\u03b5', 'varepsilon': '\u03b5', 'zeta': '\u03b6', 'eta': '\u03b7',
    'theta': '\u03b8', 'iota': '\u03b9', 'kappa': '\u03ba', 'lambda': '\u03bb',
    'mu': '\u03bc', 'nu': '\u03bd', 'xi': '\u03be', 'pi': '\u03c0',
    'rho': '\u03c1', 'sigma': '\u03c3', 'tau': '\u03c4', 'upsilon': '\u03c5',
    'phi': '\u03c6', 'varphi': '\u03c6', 'chi': '\u03c7', 'psi': '\u03c8', 'omega': '\u03c9',
    'Gamma': '\u0393', 'Delta': '\u0394', 'Theta': '\u0398', 'Lambda': '\u039b',
    'Xi': '\u039e', 'Pi': '\u03a0', 'Sigma': '\u03a3', 'Phi': '\u03a6',
    'Psi': '\u03a8', 'Omega': '\u03a9',
}

SYMBOLS = {
    'cdot': '\u22c5', 'times': '\u00d7', 'pm': '\u00b1', 'mp': '\u2213',
    'leq': '\u2264', 'geq': '\u2265', 'll': '\u226a', 'gg': '\u226b',
    'approx': '\u2248', 'neq': '\u2260', 'equiv': '\u2261', 'sim': '\u223c',
    'infty': '\u221e', 'partial': '\u2202', 'nabla': '\u2207',
    'forall': '\u2200', 'exists': '\u2203', 'in': '\u2208', 'notin': '\u2209',
    'subset': '\u2282', 'supset': '\u2283', 'cup': '\u222a', 'cap': '\u2229',
    'rightarrow': '\u2192', 'to': '\u2192', 'Rightarrow': '\u21d2',
    'leftarrow': '\u2190', 'leftrightarrow': '\u2194', 'mapsto': '\u21a6',
    'sum': '\u2211', 'prod': '\u220f', 'int': '\u222b',
    'ldots': '\u2026', 'cdots': '\u22ef', 'vdots': '\u22ee', 'ddots': '\u22f1',
    'circ': '\u2218', 'angle': '\u2220', 'perp': '\u22a5', 'parallel': '\u2225',
    'propto': '\u221d', 'emptyset': '\u2205', 'nabla': '\u2207', 'oint': '\u222e',
}


# ---------------------------------------------------------------------------
# LaTeX -> OMML parser
# ---------------------------------------------------------------------------
def _tokenize(latex):
    tokens = []
    i = 0
    n = len(latex)
    while i < n:
        c = latex[i]
        if c == '\\':
            j = i + 1
            while j < n and latex[j].isalpha():
                j += 1
            cmd = latex[i + 1:j]
            if cmd:
                tokens.append(('cmd', cmd))
            i = j
        elif c == '{':
            tokens.append(('open', '{')); i += 1
        elif c == '}':
            tokens.append(('close', '}')); i += 1
        elif c == '_':
            tokens.append(('sub', '_')); i += 1
        elif c == '^':
            tokens.append(('sup', '^')); i += 1
        elif c in ' \t':
            tokens.append(('space', c)); i += 1
        else:
            j = i
            while j < n and latex[j] not in '\\{}_^ \t':
                j += 1
            if j > i:
                tokens.append(('text', latex[i:j]))
            i = j
    return tokens


def _extract_braced(s, start):
    """Extract content of {braced group} starting at `{`. Returns (content, new_pos)."""
    if start >= len(s) or s[start] != '{':
        return '', start
    depth = 1
    i = start + 1
    content = ''
    while i < len(s) and depth > 0:
        if s[i] == '{':
            depth += 1
            if depth > 1:
                content += s[i]
        elif s[i] == '}':
            depth -= 1
            if depth > 0:
                content += s[i]
        else:
            content += s[i]
        i += 1
    return content, i


def _parse_to_omml(latex_str):
    s = latex_str.strip()
    # remove LaTeX delimiter artifacts if present
    if s.startswith('$') and s.endswith('$') and len(s) > 1:
        s = s[1:-1]
    if s.startswith('\\[') and s.endswith('\\]'):
        s = s[2:-2]
    # strip wrappers that have no OMML equivalent
    s = s.replace('\\left', '').replace('\\right', '')
    s = re_sub(r'\\mathrm\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'\1', s)
    s = re_sub(r'\\text\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'\1', s)
    s = re_sub(r'\\mathbf\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'\1', s)
    s = re_sub(r'\\mathcal\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'\1', s)
    s = re_sub(r'\\mathbb\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'\1', s)
    om = etree.Element(f'{{{M}}}oMath', nsmap=MATH_NSMAP)
    _parse_recursive(s, om)
    return om


def _parse_recursive(s, parent):
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in ' \t':
            i += 1
            continue
        if c == '\\':
            matrix_match = re_match(r'\\begin\{(bmatrix|pmatrix|matrix|vmatrix|Vmatrix|cases|aligned)\}', s[i:])
            if matrix_match:
                env = matrix_match.group(1)
                content_start = i + matrix_match.end()
                end_marker = '\\end{' + env + '}'
                content_end = s.find(end_marker, content_start)
                if content_end >= 0:
                    content = s[content_start:content_end]
                    rows = []
                    for row_source in re_split(r'\\\\', content):
                        cells = []
                        for cell_source in row_source.split('&'):
                            cell = etree.Element(f'{{{M}}}oMath')
                            _parse_recursive(cell_source.strip(), cell)
                            cells.append(cell)
                        if cells:
                            rows.append(cells)
                    matrix = _matrix(rows)
                    fences = {
                        'bmatrix': ('[', ']'), 'pmatrix': ('(', ')'),
                        'vmatrix': ('|', '|'), 'Vmatrix': ('‖', '‖'),
                        'cases': ('{', ''),
                    }
                    parent.append(_delim(*fences[env], matrix) if env in fences else matrix)
                    i = content_end + len(end_marker)
                    continue
            j = i + 1
            while j < n and s[j].isalpha():
                j += 1
            cmd = s[i + 1:j]
            i = j
            if cmd in GREEK:
                _mr(GREEK[cmd], parent)
                continue
            if cmd in SYMBOLS:
                _mr(SYMBOLS[cmd], parent)
                continue
            if cmd == 'frac':
                if i < n and s[i] == '{':
                    num, i = _extract_braced(s, i)
                    den, i = _extract_braced(s, i)
                    num_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(num, num_el)
                    den_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(den, den_el)
                    parent.append(_frac(num_el, den_el))
                continue
            if cmd == 'sqrt':
                if i < n and s[i] == '{':
                    inner, i = _extract_braced(s, i)
                    inner_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(inner, inner_el)
                    parent.append(_rad(inner_el))
                continue
            if cmd == 'dot':
                if i < n and s[i] == '{':
                    inner, i = _extract_braced(s, i)
                    inner_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(inner, inner_el)
                    parent.append(_acc('\u0307', inner_el))
                continue
            if cmd == 'ddot':
                if i < n and s[i] == '{':
                    inner, i = _extract_braced(s, i)
                    inner_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(inner, inner_el)
                    parent.append(_acc('\u0308', inner_el))
                continue
            if cmd in ('vec',):
                if i < n and s[i] == '{':
                    inner, i = _extract_braced(s, i)
                    inner_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(inner, inner_el)
                    parent.append(_acc('\u20d7', inner_el))
                continue
            if cmd in ('bar',):
                if i < n and s[i] == '{':
                    inner, i = _extract_braced(s, i)
                    inner_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(inner, inner_el)
                    parent.append(_acc('\u0304', inner_el))
                continue
            if cmd in ('hat',):
                if i < n and s[i] == '{':
                    inner, i = _extract_braced(s, i)
                    inner_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(inner, inner_el)
                    parent.append(_acc('\u0302', inner_el))
                continue
            if cmd in ('tilde',):
                if i < n and s[i] == '{':
                    inner, i = _extract_braced(s, i)
                    inner_el = etree.Element(f'{{{M}}}oMath'); _parse_recursive(inner, inner_el)
                    parent.append(_acc('\u0303', inner_el))
                continue
            # unknown command -> literal text
            _mr('\\' + cmd, parent)
            continue
        if c == '_':
            sub_text, i = _read_script(s, i)
            prev_els = list(parent)
            if prev_els:
                base = prev_els[-1]
                parent.remove(base)
                parent.append(_sub(base, sub_text))
            continue
        if c == '^':
            sup_text, i = _read_script(s, i)
            prev_els = list(parent)
            if prev_els:
                base = prev_els[-1]
                parent.remove(base)
                if base.tag == f'{{{M}}}sSub':
                    sub_el = base.find(f'{{{M}}}sub')
                    sub_text_val = ''
                    if sub_el is not None:
                        sub_r = sub_el.find(f'{{{M}}}r')
                        if sub_r is not None:
                            sub_t = sub_r.find(f'{{{M}}}t')
                            if sub_t is not None:
                                sub_text_val = sub_t.text or ''
                    base_e = base.find(f'{{{M}}}e')
                    base_inner = list(base_e)[0] if base_e is not None and len(base_e) > 0 else None
                    if base_inner is not None:
                        parent.append(_subsup(base_inner, sub_text_val, sup_text))
                else:
                    parent.append(_sup(base, sup_text))
            continue
        if c == '{':
            group, i = _extract_braced(s, i)
            group_el = etree.Element(f'{{{M}}}oMath')
            _parse_recursive(group, group_el)
            for child in list(group_el):
                parent.append(child)
            continue
        if c == '}':
            i += 1
            continue
        # regular text run
        buf = c
        i += 1
        while i < n and s[i] not in '\\{}_^ \t':
            buf += s[i]
            i += 1
        if buf.strip() or buf == ' ':
            _mr(buf, parent)


def _read_script(s, i):
    """After _ or ^ at i, read the subscript/superscript content. Returns (text, new_pos)."""
    i += 1
    if i < len(s) and s[i] == '{':
        return _extract_braced(s, i)
    if i < len(s):
        return s[i], i + 1
    return '', i


def re_sub(pat, repl, s):
    import re
    return re.sub(pat, repl, s)


def re_match(pat, s):
    import re
    return re.match(pat, s)


def re_split(pat, s):
    import re
    return re.split(pat, s)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def latex_to_oMath(latex):
    """Convert a LaTeX math string into a Word-editable <m:oMath> element."""
    math_elem = _parse_to_omml(latex)
    # apply Cambria Math to every math run (Word's native equation font)
    for mr in math_elem.findall(f'.//{{{M}}}r'):
        rPr = etree.Element(f'{{{W}}}rPr')
        rFonts = etree.SubElement(rPr, f'{{{W}}}rFonts')
        rFonts.set(f'{{{W}}}ascii', 'Cambria Math')
        rFonts.set(f'{{{W}}}hAnsi', 'Cambria Math')
        mr.insert(0, rPr)
    return math_elem


def insert_display_equation(doc, latex):
    """Append a centered DISPLAY equation paragraph (real, editable oMath)."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(6)
    math_elem = latex_to_oMath(latex)
    omath_para = etree.Element(f'{{{M}}}oMathPara', nsmap={'m': M})
    omath_para.append(math_elem)
    p._element.append(omath_para)
    return p


def insert_inline_equation(paragraph, latex):
    """Insert an INLINE equation run inside an existing paragraph (editable)."""
    run = paragraph.add_run()
    math_elem = latex_to_oMath(latex)
    run._element.append(math_elem)
    return run


def eq_text(latex_str):
    """Best-effort LaTeX -> Unicode for fallback/inline-plain rendering."""
    import re
    s = latex_str
    for cmd, char in sorted(GREEK.items(), key=lambda x: -len(x[0])):
        s = s.replace('\\' + cmd, char)
    for cmd, char in sorted(SYMBOLS.items(), key=lambda x: -len(x[0])):
        s = s.replace('\\' + cmd, char)
    s = re.sub(r'\\mathrm\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\text\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\mathcal\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\mathbb\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', r'\1/\2', s)
    s = re.sub(r'\\dot\{([^}]*)\}', lambda m: m.group(1) + '\u0307', s)
    s = re.sub(r'\\ddot\{([^}]*)\}', lambda m: m.group(1) + '\u0308', s)
    s = s.replace('\\left', '').replace('\\right', '')
    return s


if __name__ == '__main__':
    # quick self-test when run directly
    from docx import Document
    d = Document()
    insert_display_equation(d, r'\frac{a^2 + b^2}{c} = \sqrt{x_i^2 + \sum_{k=1}^{n} \alpha_k}')
    insert_display_equation(d, r'E = m c^2 \quad \int_0^\infty e^{-x}\,dx')
    insert_inline_equation(d.add_paragraph(), r'\lambda_{\max} \leq \gamma')
    d.save('omml_self_test.docx')
    print('self-test wrote omml_self_test.docx')
