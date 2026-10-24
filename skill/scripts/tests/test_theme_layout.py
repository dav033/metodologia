import re
import unittest
from pathlib import Path

import bt_pages

CSS = (Path(__file__).resolve().parents[2] / "assets" / "style.css").read_text(encoding="utf-8")


class ThemeForcing(unittest.TestCase):
    def test_layout_reads_theme_from_the_query_string(self):
        html = bt_pages.layout("T", "<p>x</p>")
        script = (Path(__file__).resolve().parents[2] / "assets" / "theme.js").read_text(encoding="utf-8")
        self.assertIn('/static/theme.js', html)
        self.assertIn("get('theme')", script)
        self.assertIn("dataset.theme = t", script)
        self.assertLess(html.index("/static/theme.js"), html.index("style.css"))  # before paint: no wrong-theme flash

    def test_both_forced_themes_exist_in_the_stylesheet(self):
        self.assertIn(':root[data-theme="dark"]', CSS)
        self.assertRegex(CSS, r':root:not\(\[data-theme="light"\]\)')
        dark_blocks = re.findall(r"--bg: #1e1e2e", CSS)
        self.assertEqual(len(dark_blocks), 2)        # the media-query copy and the forced copy stay in step


if __name__ == "__main__":
    unittest.main()


class VendoredComponents(unittest.TestCase):
    """Shoelace is vendored (MIT, version pinned, license kept) and loaded from our own server: no CDN at runtime."""

    ROOT = Path(__file__).resolve().parents[2] / "assets" / "vendor" / "shoelace-2.20.1"

    def test_files_and_license_are_in_the_repository(self):
        for name in ("shoelace-autoloader.js", "LICENSE.md", "themes/light.css", "themes/dark.css",
                     "components/tooltip/tooltip.js", "components/badge/badge.js", "components/progress-bar/progress-bar.js"):
            self.assertTrue((self.ROOT / name).is_file(), name)
        self.assertIn("MIT", (self.ROOT / "LICENSE.md").read_text(encoding="utf-8"))

    def test_layout_loads_it_locally_and_marks_the_dark_theme_class(self):
        html = bt_pages.layout("T", "x")
        theme = (Path(__file__).resolve().parents[2] / "assets" / "theme.js").read_text(encoding="utf-8")
        self.assertIn('/static/vendor/shoelace-2.20.1/shoelace-autoloader.js', html)
        self.assertIn("sl-theme-dark", theme)
        self.assertNotIn("cdn.jsdelivr", html)

    def test_no_runtime_cdn_in_our_own_pages_and_assets(self):
        for name in ("live.js", "flow.js", "flow-core.js"):
            text = (self.ROOT.parents[1] / name).read_text(encoding="utf-8")
            found = re.search(r"https?://(?!127\.0\.0\.1|www\.w3\.org/2000/svg)\S+", text)   # the SVG namespace is no request
            self.assertIsNone(found, f"{name}: {found and found.group(0)}")


class LocalFonts(unittest.TestCase):
    ASSETS = Path(__file__).resolve().parents[2] / "assets"

    def test_stylesheet_makes_no_third_party_request_and_every_font_file_exists(self):
        css = (self.ASSETS / "style.css").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"https?://", css))
        fonts = (self.ASSETS / "vendor" / "fonts" / "fonts.css").read_text(encoding="utf-8")
        files = re.findall(r"url\(([^)]+\.woff2)\)", fonts)
        self.assertGreaterEqual(len(files), 12)
        for name in files:
            self.assertTrue((self.ASSETS / "vendor" / "fonts" / name).is_file(), name)
        self.assertTrue((self.ASSETS / "vendor" / "fonts" / "LICENSE.txt").is_file())
