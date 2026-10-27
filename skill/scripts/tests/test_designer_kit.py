"""The Designer's david-ui stand-in kit: token contrast, snippet hygiene, manifest, inlining and the render audit."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "agents/designer/skills/david-ui-kit/kit"
sys.path.insert(0, str(KIT))
import audit_mockup  # noqa: E402
import contrast  # noqa: E402
import inline  # noqa: E402

P1 = ["Button", "Card", "Badge", "Avatar", "Field", "Input", "Textarea", "Select", "Checkbox", "Switch", "Combobox",
      "Sidebar", "Tabs", "Dropdown Menu", "Breadcrumb", "Pagination", "Dialog", "Alert Dialog", "Sheet", "Popover",
      "Tooltip", "Accordion", "Alert", "Toast", "Skeleton", "Spinner", "Empty", "Table", "Data Table", "Chart"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SVG_SELF = {"path", "circle", "rect", "line", "polyline"}
NETWORK = re.compile(r"""(src|href)\s*=\s*["']?\s*(https?:)?//|url\(|@import|fetch\(|XMLHttpRequest""", re.I)


class Tags(HTMLParser):
    """Collects tag balance problems, classes, inline styles, handlers and scripts of a snippet."""

    def __init__(self):
        super().__init__()
        self.stack, self.errors, self.classes, self.styles, self.handlers, self.scripts = [], [], set(), [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.classes.update((a.get("class") or "").split())
        if a.get("style"):
            self.styles.append(a["style"])
        self.handlers += [k for k in a if k.startswith("on")]
        self.scripts += tag == "script"
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}> (open: {self.stack[-3:]})")
            return
        self.stack.pop()


def kit_classes() -> set[str]:
    css = re.sub(r"/\*.*?\*/", "", (KIT / "components.css").read_text(), flags=re.S)
    return set(re.findall(r"\.([a-zA-Z][\w-]*)", re.sub(r"url\([^)]*\)|\d+\.\d+", "", css)))


def manifest() -> dict:
    return json.loads((KIT / "components/manifest.json").read_text())


class Tokens(unittest.TestCase):
    def test_kit_tokens_pass_aa_in_both_themes(self):
        rows, problems = contrast.check((KIT / "tokens.css").read_text())
        self.assertEqual(problems, [])
        self.assertEqual({r[0] for r in rows}, {"light", "dark"})
        self.assertGreater(len(rows), 140)

    def test_a_weak_override_fails_and_cascade_order_counts(self):
        css = (KIT / "tokens.css").read_text()
        _, problems = contrast.check(css + '\n[data-theme="dark"] { --muted-foreground: #585b70; }')
        self.assertTrue(any("dark: --muted-foreground on --muted" in p for p in problems), problems)
        # a later bare :root block also lands in dark, like the browser cascade
        _, problems = contrast.check(css + "\n:root { --foreground: #777777; }")
        self.assertTrue(any(p.startswith("dark: --foreground on --background") for p in problems), problems)
        self.assertTrue(any(p.startswith("light: --foreground on --background") for p in problems), problems)
        # rules inside @media do not count, a missing role is reported
        _, problems = contrast.check(css + "\n@media (min-width: 1px) { :root { --foreground: #ffffff; } }")
        self.assertEqual(problems, [])
        _, problems = contrast.check(":root { --foreground: #000000; }")
        self.assertTrue(any("--background is missing" in p for p in problems))

    def test_contrast_cli_reads_a_mockup(self):
        out = subprocess.run([sys.executable, str(KIT / "contrast.py"), str(KIT / "reference/acceso.html")],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertIn("all pass", out.stdout)

    def test_components_use_roles_only(self):
        css = re.sub(r"/\*.*?\*/", "", (KIT / "components.css").read_text(), flags=re.S)
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\boklch\(", css))
        defined = set(re.findall(r"--([\w-]+)\s*:", (KIT / "tokens.css").read_text() + css))
        used = set(re.findall(r"var\(--([\w-]+)", css))
        self.assertEqual(used - defined, set())


class Snippets(unittest.TestCase):
    def test_manifest_matches_files_and_covers_the_p1_inventory(self):
        data = manifest()
        rows = data["components"]
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({r["file"] for r in rows}, {p.name for p in (KIT / "components").glob("*.html")})
        cats = {c["id"] for c in data["categories"]}
        self.assertTrue(all(r["category"] in cats for r in rows))
        self.assertEqual(sorted(r["name"] for r in rows if r["priority"] == "P1"), sorted(P1))
        for r in rows:
            self.assertTrue(r["states"] and r["contract"].startswith(r["name"].replace(" ", "")), r["id"])
        for ref in data["references"]:
            self.assertTrue((KIT / ref["file"]).is_file(), ref)

    def test_every_snippet_is_well_formed_offline_and_uses_kit_classes(self):
        known = kit_classes()
        for path in sorted((KIT / "components").glob("*.html")):
            text = path.read_text()
            examples = re.findall(r"<!-- example: ([a-z0-9-]+) \| [^>]+ -->", text)
            self.assertTrue(examples, path.name)
            self.assertEqual(len(examples), len(set(examples)), path.name)
            p = Tags()
            p.feed(text)
            p.close()
            p.stack = [t for t in p.stack if t not in SVG_SELF]
            self.assertEqual((p.errors, p.stack), ([], []), path.name)
            self.assertEqual(p.classes - known, set(), path.name)
            self.assertEqual((p.handlers, p.scripts), ([], 0), path.name)
            self.assertIsNone(NETWORK.search(text), path.name)
            for style in p.styles:                               # layout sizes only, never a colour
                self.assertIsNone(re.search(r"#[0-9a-f]{3}|rgb|hsl|color|background", style, re.I), (path.name, style))
            ids = re.findall(r'\bid="([^"]+)"', text)
            self.assertEqual(len(ids), len(set(ids)), path.name)

    def test_kit_script_is_offline(self):
        self.assertIsNone(NETWORK.search((KIT / "kit.js").read_text()))


class Inline(unittest.TestCase):
    def test_references_carry_the_current_kit_and_the_select_contract(self):
        for ref in manifest()["references"]:
            text = (KIT / ref["file"]).read_text()
            self.assertEqual(inline.inline(text), text, f"{ref['file']}: run kit/inline.py")
            fails, warns = audit_mockup.static_checks(text)
            self.assertEqual((fails, warns), ([], []), ref["file"])
            classes = Tags()
            classes.feed(text)
            self.assertEqual(classes.classes - kit_classes(), set(), ref["file"])

    def test_template_has_markers_and_inline_is_idempotent(self):
        text = (KIT / "templates/mockup.html").read_text()
        self.assertIn("<!-- kit:css -->", text)
        self.assertIn("<!-- kit:js -->", text)
        once = inline.inline(text)
        self.assertEqual(inline.inline(once), once)
        self.assertIn('<style data-kit="css">', once)
        self.assertNotIn("<!-- kit:css -->", once)
        with self.assertRaises(ValueError):
            inline.inline("<html><head></head></html>")

    def test_check_flag_reports_an_outdated_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "m.html"
            page.write_text(inline.inline((KIT / "templates/mockup.html").read_text()).replace("--spacing: 0.25rem", "--spacing: 1px"))
            out = subprocess.run([sys.executable, str(KIT / "inline.py"), "--check", str(page)], capture_output=True, text=True)
            self.assertEqual(out.returncode, 1)
            self.assertIn("outdated", out.stdout)


class AuditStatic(unittest.TestCase):
    def test_network_reference_and_missing_selects(self):
        fails, warns = audit_mockup.static_checks('<link rel="stylesheet" href="https://cdn.example.com/x.css"><img src="//x/y.png">')
        self.assertEqual(len(fails), 2)
        self.assertTrue(any("no kit block" in w for w in warns))
        self.assertTrue(any('select id="view"' in w for w in warns))

    def test_combos_cover_every_axis_and_trim_evenly(self):
        plan, total, base = audit_mockup.combos(["a", "b"], ["s1", "s2"], ["", "d"], ["light", "dark"], 100)
        self.assertEqual((len(plan), total, base), (12, 12, ""))
        self.assertIn(("dark", "b", "s1", "d"), plan)
        plan, total, _ = audit_mockup.combos(["v"] * 30, ["s"] * 10, [], ["light", "dark"], 50)
        self.assertEqual((len(plan), total), (50, 600))

    def test_without_playwright_it_says_not_run(self):
        code = ("import sys, runpy; sys.modules['playwright'] = None; sys.argv = ['audit_mockup.py', sys.argv[1]]; "
                f"runpy.run_path({str(KIT / 'audit_mockup.py')!r}, run_name='__main__')")
        out = subprocess.run([sys.executable, "-c", code, str(KIT / "reference/acceso.html")], capture_output=True, text=True)
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("AUDIT NOT RUN: Playwright is not installed", out.stdout)
        self.assertNotIn("PASS", out.stdout)

    def test_missing_file_is_not_run(self):
        self.assertEqual(audit_mockup.main(["/nonexistent/mockup.html"]), 2)


FAILING = """<!doctype html><html lang="es" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<style>
body { margin: 0; font: 14px/1.5 sans-serif; background: #ffffff; color: #222222; }
.col { width: 420px; margin: 40px auto; display: flex; flex-direction: column; gap: 12px; }
.faint { color: #b5b5b5; }
.link { text-align: center; }
.box { background: #e8e8f0; padding: 2px 3px; border-radius: 6px; }
.field { border: 1px solid #eeeeee; height: 36px; padding: 0 10px; }
.wide { width: 900px; }
footer { padding: 24px 40px; }
.shadowbtn, .shadowbtn:focus, .shadowbtn:focus-visible { outline: none; box-shadow: 0 2px 4px rgb(0 0 0 / .8); }
.flat { padding: 0; border: 1px solid #333333; height: 32px; }
.pale { color: oklch(0.86 0 0); }
html[data-theme="dark"] body { background: #1e1e2e; color: #cdd6f4; }
</style></head><body>
<header id="bar"><label for="view">Vista</label><select id="view"><option value="a">A</option></select>
<label for="theme">Tema</label><select id="theme"><option value="light">Claro</option><option value="dark">Oscuro</option></select></header>
<main id="app"><div class="col"><h1>Iniciar sesión</h1><p>Usa el correo con el que te invitaron.</p>
<label for="e">Correo</label><input id="e" class="field" value="ana@example.com"><p class="faint">Texto tenue que casi no se lee.</p>
<p class="link"><a href="#">¿Olvidaste tu contraseña?</a></p><div class="box">Caja apretada con texto pegado al borde</div>
<p class="pale">Texto oklch casi blanco</p><button class="shadowbtn">Botón sin foco visible</button><input class="flat" aria-label="Plano" value="Sin margen"></div>
<div class="wide">Contenido demasiado ancho para un teléfono.</div></main>
<footer>Pictures · Piloto</footer>
<script>document.getElementById('theme').addEventListener('change', e => document.documentElement.dataset.theme = e.target.value);</script>
</body></html>"""


NOMAIN = """<!doctype html><html lang="es"><head><meta charset="utf-8"><style>body { background: #ffffff; color: #222222; }
.pale { color: #dddddd; }</style></head><body><div class="wrap">
<label>Vista <select id="view"><option value="a">A</option></select></label>
<label>Tema <select id="theme"><option value="light">Claro</option></select></label>
<h1>Pantalla</h1><p class="pale">Texto pálido</p></div></body></html>"""


@unittest.skipUnless(shutil.which("uv") and (shutil.which("chromium") or shutil.which("google-chrome")),
                     "needs uv and a Chromium to render")
class AuditRender(unittest.TestCase):
    def audit(self, path: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(["uv", "run", "-q", "--with", "playwright", "python", str(KIT / "audit_mockup.py"), str(path),
                               "--json", str(path.with_suffix(".json")), *extra], capture_output=True, text=True, timeout=600)

    def test_failing_fixture_reports_each_defect(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "bad.html"
            page.write_text(FAILING)
            out = self.audit(page)
            self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
            kinds = {r["kind"]: r for r in json.loads(page.with_suffix(".json").read_text())["findings"]}
            for kind in ("contrast", "nontext", "alignment", "padding", "overflow"):
                self.assertIn(kind, kinds, out.stdout)
            rows = json.loads(page.with_suffix(".json").read_text())["findings"]
            def has(kind, text):
                return any(r["kind"] == kind and text in f"{r['el']} {r.get('detail', '')}" for r in rows)
            self.assertTrue(has("alignment", "Olvidaste"), out.stdout)              # inline link alone in a centred line
            self.assertTrue(has("alignment", "Pictures · Piloto"), out.stdout)      # footer on another x
            self.assertTrue(has("contrast", "oklch"), out.stdout)                   # modern colour syntax is measured
            self.assertTrue(has("focus", "shadowbtn"), out.stdout)                  # an unchanged shadow is not focus
            self.assertTrue(has("padding", "Sin margen"), out.stdout)               # field text on its edge
            self.assertTrue(has("padding", "screen edge"), out.stdout)              # 390 px gutter
            self.assertIn("RESULT: FAIL", out.stdout)

    def test_selects_inside_the_product_still_measure_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "nomain.html"
            page.write_text(NOMAIN)
            out = self.audit(page, "--widths", "1280")
            self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
            rows = json.loads(page.with_suffix(".json").read_text())["findings"]
            self.assertTrue(any(r["kind"] == "contrast" and "pálido" in r["el"] for r in rows), out.stdout)
            self.assertIn("no <main> or #app", out.stdout)

    def test_no_keyboard_stop_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "static.html"
            page.write_text('<!doctype html><html><body><main id="app"><h1>Hola</h1><p>Texto legible.</p></main></body></html>')
            out = self.audit(page, "--widths", "1280")
            self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
            self.assertIn("focus not measured", out.stdout)

    def test_reference_mockup_passes(self):
        out = self.audit(KIT / "reference/acceso.html", "--widths", "1280,390")
        Path(KIT / "reference/acceso.json").unlink(missing_ok=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("RESULT: PASS", out.stdout)

    def test_unknown_browser_is_not_run(self):
        out = self.audit(KIT / "reference/acceso.html", "--browser", "/nonexistent/chromium")
        Path(KIT / "reference/acceso.json").unlink(missing_ok=True)
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("AUDIT NOT RUN", out.stdout)


if __name__ == "__main__":
    unittest.main()
