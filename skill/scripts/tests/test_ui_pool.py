"""`@bitacora/ui`: the package, project themes, the pool build and live mockups (D-280).

The owner, 2026-10-31: the metodologia pool is the single source of UI components, and «si hago un cambio en los
componentes de metodologia eso debería cambiar automáticamente los estilos de un mockup antiguo». The build checks run
in a scratch kit workspace whose node_modules is the installed toolchain (read-only), never writing into it."""
from __future__ import annotations

import http.client
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import bt_kit_workspace
import bt_ui

LIVE_WS = bt_kit_workspace.workspace()
TOOLCHAIN = (LIVE_WS / "node_modules").is_dir() and shutil.which("node") is not None
REFERENCE = bt_ui.REAL / "reference" / "acceso.tsx"


class Package(unittest.TestCase):
    def test_every_manifest_import_of_the_pool_resolves_to_a_package_source(self):
        manifest = json.loads((bt_ui.REAL / "manifest.json").read_text(encoding="utf-8"))
        exports = bt_ui.package()["exports"]
        seen = 0
        for row in manifest["entries"]:
            for spec in re.findall(r'from "(@bitacora/ui/[^"]+)"', row["import"]):
                rest = spec[len("@bitacora/ui/"):]
                self.assertTrue((bt_ui.SRC / f"{rest}.tsx").is_file() or (bt_ui.SRC / f"{rest}.ts").is_file(), spec)
                seen += 1
            self.assertNotIn('"@/', row["import"], row["id"])
        self.assertGreaterEqual(seen, 80)
        self.assertEqual(exports["./components/*"], "./src/components/*.tsx")
        self.assertEqual(bt_ui.package()["name"], "@bitacora/ui")

    def test_no_pool_source_imports_through_the_workspace_alias(self):
        offenders = [p for p in bt_ui.SRC.rglob("*.ts*") if re.search(r"""from\s+["']@/""", p.read_text(encoding="utf-8"))]
        self.assertEqual(offenders, [])
        checklist = (bt_ui.SRC / "components/bencho/checklist/Checklist.tsx").read_text(encoding="utf-8")
        self.assertTrue(checklist.startswith('import "./Checklist.css";'))

    def test_structure_holds_no_colour_values_and_every_role_it_maps_has_a_default(self):
        styles = (bt_ui.SRC / "styles.css").read_text(encoding="utf-8")
        theme = (bt_ui.SRC / "theme.css").read_text(encoding="utf-8")
        mapped = set(re.findall(r"--color-[\w-]+:\s*var\((--[\w-]+)\)", styles))
        self.assertIn("--primary", mapped)
        for role in mapped | {"--ui-font-sans", "--ui-font-mono"}:
            self.assertIn(f"{role}:", theme, role)
        self.assertNotRegex(styles.split("@theme inline")[0], r":root,\s*\[data-theme=\"light\"\]\s*{[^}]*#[0-9a-f]{6}")
        for line in styles.splitlines():
            if line.startswith("@import"):
                self.assertRegex(line, r'@import "\./vendor/')
        # Bencho's triplets come from the theme's triplet roles: no theme colour is written as numbers here
        for role in set(re.findall(r"var\((--[\w-]+-rgb)\)", styles)):
            self.assertIn(f"{role}:", theme, role)
        for triplet in re.findall(r"\b(\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\b", styles):
            self.assertIn(set(triplet), ({"0"}, {"255"}), triplet)
        for color in re.findall(r"rgba?\(\s*(\d{1,3})[ ,]+(\d{1,3})[ ,]+(\d{1,3})", styles):
            self.assertIn(set(color), ({"0"}, {"255"}), color)

    def test_rewrite_and_registry_keys(self):
        src = Path("/p/src")
        text = 'import { Button } from "@/components/ui/button"\nimport x from \'@/components/theme-provider.tsx\''
        out = bt_ui.rewrite_imports(text, src / "components/ui", src)
        self.assertIn('from "./button"', out)
        self.assertIn("from '../theme-provider'", out)
        self.assertEqual(bt_ui.registry_key("@/components/ui/button"), "@bitacora/ui/components/ui/button")
        self.assertEqual(bt_ui.registry_key("@bitacora/ui/components/ui/button.tsx"), "@bitacora/ui/components/ui/button")
        self.assertIsNone(bt_ui.registry_key("react"))

    def test_digest_follows_every_byte_and_the_project_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            ui = Path(tmp) / "ui"
            shutil.copytree(bt_ui.UI, ui)
            with patch.object(bt_ui, "UI", ui), patch.object(bt_ui, "SRC", ui / "src"), \
                    patch.object(bt_ui, "THEMES", ui / "themes"):
                before = bt_ui.digest()
                self.assertEqual(before, bt_ui.digest())
                self.assertNotEqual(bt_ui.digest(bt_ui.files("pictures")), before)
                (ui / "src/components/ui/button.tsx").write_text("// changed\n", encoding="utf-8")
                self.assertNotEqual(bt_ui.digest(), before)
                self.assertRegex(bt_ui.version(), r"^1\.0\.0\+[0-9a-f]{12}$")


class Themes(unittest.TestCase):
    GLOBALS = """@import "tailwindcss";
@custom-variant apaisado (@media (orientation: landscape));
:root { color-scheme: light; --fondo: #faf9fc; --acento: #6d3fe0; --background: var(--fondo); --primary: var(--acento); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --fondo: #000; } }
:root[data-theme="dark"] { color-scheme: dark; --fondo: #0b0c10; --acento: #9479ff; }
@theme inline { --font-sans: var(--font-geist-sans); --color-fondo: var(--fondo); }
.btn { color: red; }
"""

    def test_import_extracts_light_and_dark_tokens_and_the_font_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "globals.css"
            src.write_text(self.GLOBALS, encoding="utf-8")
            with patch.object(bt_ui, "THEMES", Path(tmp) / "themes"):
                out = bt_ui.import_theme("demo", src, ["@fontsource-variable/geist"])
                text = out.read_text(encoding="utf-8")
                light, dark = text.split('.dark, [data-theme="dark"]')
                self.assertIn("--primary: var(--acento);", light)
                self.assertIn("--fondo: #faf9fc;", light)
                self.assertNotIn("#000", text)                    # media-query blocks are not the explicit theme
                self.assertIn("--fondo: #0b0c10;", dark)
                self.assertIn("color-scheme: dark;", dark)
                self.assertIn("--ui-font-sans: var(--font-geist-sans), ui-sans-serif", light)
                self.assertIn("@mockup-fonts: @fontsource-variable/geist", text)
                self.assertNotIn(".btn", text)
                self.assertEqual(bt_ui.theme_path("demo"), out)
                self.assertIsNone(bt_ui.theme_path("../demo"))
                self.assertEqual(bt_ui.theme_css("nope"), "")

    def test_import_states_the_triplet_roles_through_the_project_aliases(self):
        css = (":root { --texto: #1c1425; --superficie: #fff; --foreground: var(--texto); --card: var(--superficie);\n"
               "  --muted: rgb(239 233 248); --primary-foreground: var(--nada, #ffffff); }\n"
               ":root[data-theme=\"dark\"] { --texto: #f4f5f7; --superficie: #16181f; --muted: oklch(0.3 0 0); }\n")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "globals.css"
            src.write_text(css, encoding="utf-8")
            with patch.object(bt_ui, "THEMES", Path(tmp) / "themes"):
                light, dark = bt_ui.import_theme("demo", src).read_text(encoding="utf-8").split('.dark, [data-theme="dark"]')
                for line in ("--foreground-rgb: 28, 20, 37;", "--card-rgb: 255, 255, 255;", "--muted-rgb: 239, 233, 248;",
                             "--primary-foreground-rgb: 255, 255, 255;"):
                    self.assertIn(line, light)
                self.assertIn("--foreground-rgb: 244, 245, 247;", dark)   # the light alias, the dark token
                self.assertIn("--card-rgb: 22, 24, 31;", dark)
                self.assertNotIn("--muted-rgb", dark)                      # not plain sRGB: no triplet, not a wrong one
                src.write_text(":root { --texto: #000; }\n", encoding="utf-8")
                self.assertNotIn(".dark", bt_ui.import_theme("demo", src).read_text(encoding="utf-8"))

    def test_pictures_theme_keeps_its_own_tokens_on_the_roles(self):
        text = bt_ui.theme_path("pictures").read_text(encoding="utf-8")
        light, dark = text.split('.dark, [data-theme="dark"]')
        for role in ("--background: var(--fondo)", "--primary: var(--acento)", "--ring: var(--acento)"):
            self.assertIn(role, light)
        self.assertIn("--acento: #6d3fe0", light)
        self.assertIn("--acento: #9479ff", dark)
        self.assertIn('var(--font-geist-sans, "Geist Variable")', light)

    @unittest.skipUnless((LIVE_WS / "node_modules/@fontsource-variable/geist").is_dir(), "fontsource not installed")
    def test_mockup_fonts_are_inlined_latin_only(self):
        css = bt_ui.font_faces(["@fontsource-variable/geist", "../etc", "@fontsource-variable/nope"])
        self.assertIn("font-family: 'Geist Variable'", css)
        self.assertIn("url(data:font/woff2;base64,", css)
        self.assertNotIn("cyrillic", css)
        self.assertNotIn(".woff2)", css.replace("data:font/woff2", ""))

    def test_a_frozen_mockup_links_the_current_theme_once(self):
        html = "<html><head><style>:root{--primary:red}</style></head><body></body></html>"
        out = bt_ui.with_theme(html, "pictures")
        self.assertLess(out.index("<style>"), out.index('href="/ui/theme/pictures.css"'))
        self.assertLess(out.index("data-ui-theme"), out.index("</head>"))
        self.assertEqual(bt_ui.with_theme(out, "pictures"), out)
        self.assertEqual(bt_ui.with_theme(html, "../x"), html)


def scratch_workspace(case: unittest.TestCase) -> Path:
    """A kit workspace whose node_modules is the installed toolchain (symlink, read-only) and whose dist is new."""
    tmp = tempfile.TemporaryDirectory()
    case.addCleanup(tmp.cleanup)
    ws = Path(tmp.name) / "ws"
    ws.mkdir()
    (ws / "node_modules").symlink_to(LIVE_WS / "node_modules")
    shutil.copy2(LIVE_WS / "package.json", ws / "package.json")
    p = patch.dict(os.environ, {"BITACORA_KIT_WORKSPACE": str(ws)})
    p.start()
    case.addCleanup(p.stop)
    return ws


@unittest.skipUnless(TOOLCHAIN, "kit toolchain is not installed")
class PoolBuild(unittest.TestCase):
    def setUp(self):
        self.ws = scratch_workspace(self)

    def test_the_pool_builds_once_per_digest_with_one_registry_for_every_mockup(self):
        out = bt_ui.ensure_build()
        self.assertEqual(out, self.ws / "dist/ui" / bt_ui.digest())
        meta = json.loads((out / "bitacora-ui.json").read_text())
        for key in ("@bitacora/ui/components/ui/button", "@bitacora/ui/components/react-bits/BlurText", "react",
                    "react-dom/client", "@kit/mockup", "motion/react", "@base-ui/react/button"):
            self.assertIn(key, meta["keys"])
        self.assertNotIn("lucide-react", meta["keys"])            # stateless: stays inside whatever imports it
        self.assertIn("window.__bitacoraUI", (out / "bitacora-ui.js").read_text())
        self.assertIn("var(--primary)", (out / "bitacora-ui.css").read_text())
        with patch.object(bt_ui, "_node", side_effect=AssertionError("rebuilt")):
            self.assertEqual(bt_ui.ensure_build(), out)
            self.assertEqual(bt_ui.pool_file("current", "bitacora-ui.js"), out / "bitacora-ui.js")
        self.assertIsNone(bt_ui.pool_file("current", "../../etc/passwd"))
        self.assertIsNone(bt_ui.pool_file("../x", "bitacora-ui.js"))

    def test_a_live_mockup_reads_components_and_theme_from_the_pool_and_restyles_when_the_pool_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ui = Path(tmp) / "ui"
            shutil.copytree(bt_ui.UI, ui)
            tsx = Path(tmp) / "acceso@v1.tsx"
            shutil.copy2(REFERENCE, tsx)
            with patch.object(bt_ui, "UI", ui), patch.object(bt_ui, "SRC", ui / "src"), \
                    patch.object(bt_ui, "THEMES", ui / "themes"):
                page = bt_ui.live_mockup("pictures", tsx)
                d = bt_ui.digest()
                self.assertIn(f'src="/ui/{d}/bitacora-ui.js"', page)
                self.assertIn(f'href="/ui/{d}/bitacora-ui.css"', page)
                self.assertIn('href="/ui/theme/pictures.css"', page)
                self.assertLess(page.index(f"/ui/{d}/bitacora-ui.css"), page.index("/ui/theme/pictures.css"))
                self.assertLess(len(page), 150_000)                       # the components are not inlined
                self.assertNotIn("react.production", page)
                with patch.object(bt_ui, "_node", side_effect=AssertionError("rebuilt")):
                    self.assertEqual(bt_ui.live_mockup("pictures", tsx), page)    # cached by source, pool, project
                (ui / "src/components/ui/button.tsx").write_text(
                    (ui / "src/components/ui/button.tsx").read_text() + "\n// pool change\n")
                again = bt_ui.live_mockup("pictures", tsx)
                self.assertNotEqual(bt_ui.digest(), d)
                self.assertIn(f"/ui/{bt_ui.digest()}/bitacora-ui.js", again)  # the same old TSX, the new pool
                self.assertIsNone(bt_ui.live_mockup("pictures", Path(tmp) / "missing.tsx"))
                broken = Path(tmp) / "broken.tsx"
                broken.write_text("import { Nope } from '@bitacora/ui/components/ui/nope';\nmountMockup(Nope, {});\n")
                self.assertIsNone(bt_ui.live_mockup("pictures", broken))

    def test_the_export_inlines_the_project_theme(self):
        out = self.ws / "acceso.html"
        self.assertEqual(bt_kit_workspace.mockup_build(str(REFERENCE), str(out), "", "pictures"), 0)
        text = out.read_text()
        self.assertIn("--acento:#6d3fe0", text.replace(" ", ""))
        self.assertNotIn('<script src=', text)


class Server(unittest.TestCase):
    """The panel serves the pool and the theme, and a mockup with a TSX source live, under a CSP that allows only
    `/ui/` besides inline code."""

    def setUp(self):
        import bt_core
        import bt_server
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        for target, attr, value in ((bt_server, "ROOT", root), (bt_core, "ROOT", root),
                                    (bt_server, "STATE", root / ".state"), (bt_core, "STATE", root / ".state")):
            p = patch.object(target, attr, value)
            p.start()
            self.addCleanup(p.stop)
        self.design = root / "pictures/requirements/REQ-001-test/design"
        self.design.mkdir(parents=True)
        (self.design.parent / "PLAN.md").write_text("---\nstatus: review\n---\n# Plan\n", encoding="utf-8")
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=120)
        c.request("GET", path)
        r = c.getresponse()
        return r.status, r.getheader("Content-Security-Policy") or "", r.getheader("Content-Type") or "", r.read().decode()

    def test_theme_route_and_a_frozen_mockup_with_the_theme_linked(self):
        status, _, ctype, body = self.get("/ui/theme/pictures.css")
        self.assertEqual((status, ctype.split(";")[0]), (200, "text/css"))
        self.assertIn("--primary: var(--acento)", body)
        self.assertEqual(self.get("/ui/theme/..%2Fx.css")[3], "")
        self.assertEqual(self.get("/ui/nope/bitacora-ui.js")[0], 404)
        (self.design / "frozen@v1.html").write_text("<html><head><style>x{}</style></head><body>hi</body></html>")
        status, csp, _, body = self.get("/p/pictures/req/REQ-001/mockup?contract=frozen@v1")
        self.assertEqual(status, 200)
        self.assertTrue(csp.startswith("sandbox allow-scripts"))
        self.assertIn(f"script-src 'unsafe-inline' {self.base}/ui/;", csp)
        self.assertIn(f"style-src 'unsafe-inline' {self.base}/ui/;", csp)
        self.assertIn('href="/ui/theme/pictures.css" data-ui-theme', body)

    @unittest.skipUnless(TOOLCHAIN and shutil.which("uv") and shutil.which("chromium"),
                         "kit toolchain or cached Playwright/Chromium unavailable")
    def test_an_old_mockup_renders_live_and_follows_a_theme_change(self):
        scratch_workspace(self)
        tmp = Path(self.tmp.name)
        ui = tmp / "ui-copy"
        shutil.copytree(bt_ui.UI, ui)
        for name, value in (("UI", ui), ("SRC", ui / "src"), ("THEMES", ui / "themes")):
            p = patch.object(bt_ui, name, value)
            p.start()
            self.addCleanup(p.stop)
        shutil.copy2(REFERENCE, self.design / "acceso@v1.tsx")
        (self.design / "acceso@v1.html").write_text("<html><head></head><body>FROZEN EXPORT</body></html>")
        status, _, _, body = self.get("/p/pictures/req/REQ-001/mockup?contract=acceso@v1")
        self.assertEqual(status, 200)
        self.assertNotIn("FROZEN EXPORT", body)
        self.assertIn("data-ui-live", body)
        script = '''
import sys
from playwright.sync_api import sync_playwright
url, exe, theme = sys.argv[1], sys.argv[2], sys.argv[3]
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=exe)
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.goto(url)
    page.wait_for_selector("#app button", timeout=15000)
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    btn = page.evaluate("getComputedStyle(document.querySelector('[data-slot=button]')).backgroundColor")
    print("BG", bg, "BTN", btn, "ERRORS", len(errors), errors[:3])
    browser.close()
'''
        def render():
            done = subprocess.run(["uv", "run", "--no-project", "--offline", "--with", "playwright", "python", "-c", script,
                                   f"{self.base}/p/pictures/req/REQ-001/mockup?contract=acceso@v1",
                                   shutil.which("chromium"), "x"], capture_output=True, text=True, timeout=180,
                                  env={**os.environ, "UV_OFFLINE": "1"})
            self.assertEqual(done.returncode, 0, done.stdout[-2000:] + done.stderr[-2000:])
            return done.stdout
        first = render()
        self.assertIn("BG rgb(250, 249, 252)", first)                  # pictures' --fondo through --background
        self.assertIn("ERRORS 0", first)
        theme = ui / "themes/pictures.css"
        theme.write_text(theme.read_text().replace("--fondo: #faf9fc;", "--fondo: #102030;", 1))
        second = render()                                                # the same mockup file, a new theme
        self.assertIn("BG rgb(16, 32, 48)", second)


if __name__ == "__main__":
    unittest.main()
