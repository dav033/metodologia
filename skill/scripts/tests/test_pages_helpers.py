import unittest
from pathlib import Path

import bt_pages

ASSETS = Path(__file__).resolve().parents[2] / "assets"


class InlineText(unittest.TestCase):
    def test_code_spans_render_and_everything_else_stays_escaped(self):
        html = bt_pages.inline("Pool (`src/lib/db.ts`) and <script>alert(1)</script> `a<b`")
        self.assertIn("<code>src/lib/db.ts</code>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("<code>a&lt;b</code>", html)
        self.assertNotIn("<script>", html)

    def test_empty_title_is_empty(self):
        self.assertEqual(bt_pages.inline(None), "")


class CountChips(unittest.TestCase):
    def test_singular_plural_and_zero(self):
        self.assertEqual(bt_pages.kpi(1, "activo", "activos"), '<span class="kpi">1 activo</span>')
        self.assertEqual(bt_pages.kpi(3, "activo", "activos"), '<span class="kpi">3 activos</span>')
        self.assertEqual(bt_pages.kpi(0, "activo", "activos"), '<span class="kpi zero">0 activos</span>')


class Layout(unittest.TestCase):
    def test_skip_link_main_target_and_page_enhancements(self):
        html = bt_pages.layout("T", "<p>x</p>")
        self.assertLess(html.index('href="#main"'), html.index('<header'))
        self.assertIn('<main id="main"', html)
        self.assertIn('/static/enhance.js', html)

    def test_every_imported_stylesheet_exists(self):
        import re
        for name in re.findall(r'@import url\("([^"]+)"\)', (ASSETS / "style.css").read_text(encoding="utf-8")):
            self.assertTrue((ASSETS / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
