import unittest
import fitz

from server import block_order, is_display_formula, merge_display_formula_blocks
from vector_math import vector_formula_to_latex


def formulas_on_page(path, page_number):
    pdf = fitz.open(path)
    page = pdf[page_number - 1]
    blocks = block_order(page.get_text("dict")["blocks"], page.rect.width)
    blocks = merge_display_formula_blocks(blocks, page.rect.width)
    return [vector_formula_to_latex(b) for b in blocks if b.get("type") == 0 and is_display_formula(b, page.rect.width)]


class VectorMathTests(unittest.TestCase):
    def test_arxiv_page_three_formula_recovery(self):
        formulas = formulas_on_page("../tmp/pdfs/2505.13527v4.pdf", 3)
        joined = "\n".join(formulas)
        self.assertIn(r"X_{\mathrm{harmful}} \subset D_{\mathrm{aligned}}", joined)
        self.assertIn(r"\operatorname{Sim} (x_{\mathrm{harmful}}, x_{\mathrm{harmful}}^{\prime}) \geq \tau", joined)
        self.assertIn(r"\max_{F}", joined)
        self.assertIn(r"\notin Y_{\mathrm{refuse}}", joined)
        self.assertIn(r"F: X_{\mathrm{harmful}} \to X_{\mathrm{logic}}", joined)
        self.assertIn(r"X_{\mathrm{logic}} \cap D_{\mathrm{aligned}} \approx \emptyset", joined)
        self.assertNotIn("A jailbreak task", joined)


if __name__ == "__main__":
    unittest.main()
