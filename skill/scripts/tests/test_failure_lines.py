"""The note a retry reads after a failed verification must carry the line that says WHY, wherever the output buried it.

pictures REQ-021 T2.6 att-0095 (24 attempts): the Playwright line `locator.waitFor: Timeout 30000ms exceeded.` sat above ~3 KB of
JSON server logs, the 1500-char tail started after it and no error pattern matched it, so the agent read only logs and build
banners. T3.11 att-0093: a check imported a source file the agent never created and the note called it a dependency problem.
att-0088: Node ran out of heap inside the sandbox, an environment limit, not a code defect. The fixtures below keep the
structure of those real outputs (sanitized and shortened); the JSON lines are generated to bury the decisive line as it was.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bt_scheduler_quality_adapter import QualityVerificationPort

NPM_NOTICE = ("npm notice\nnpm notice New major version of npm available! 11.19.0 -> 12.2.1\n"
              "npm notice To update run: npm install -g npm@12.2.1\nnpm notice\n")
BUILD_BANNERS = ("\n> @acme/core@0.1.0 build\n> tsc -p tsconfig.build.json\n\n\nGenerating route types...\n"
                 "✓ Types generated successfully\n\n> demo@0.1.0 accounts:test-ui\n"
                 "> tsx --conditions=react-server scripts/test/test-accounts-ui.ts\n")
NEXT_BANNERS = "▲ Next.js 16.3.0\n- Local:         http://127.0.0.1:41293\n✓ Ready in 164ms\n✓ Running next.config.ts took 43ms\n"


def json_logs(count: int, level: str = "info") -> str:
    flags = {"node_env": "production", **{f"FLAG_{n}_V1": n % 3 != 0 for n in range(14)}}
    lines = [json.dumps({"evento": "effective_flags", "servicio": "next", **flags}, separators=(",", ":"))]
    for n in range(count):
        lines.append(json.dumps({"ts": f"2026-10-28T19:41:{10 + n:02d}.031Z", "nivel": level, "servicio": "next",
                                 "entorno": "vercel", "evento": "peticion.fin", "solicitud": f"00000000-0000-4000-8000-{n:012d}",
                                 "ruta": "/api/workshop/sheet", "ms": 510 + n,
                                 "datos": {"metodo": "GET", "estado": 200, "tipoContenido": "application/json"}},
                                separators=(",", ":")))
    return "\n".join(lines) + "\n"


ATT_0095 = (NPM_NOTICE + "locator.waitFor: Timeout 30000ms exceeded.\nCall log:\n"
            "  - waiting for getByRole('heading', { name: 'Enlace de invitación', exact: true }) to be visible\n\n"
            "Server diagnostic tail:\n" + NEXT_BANNERS + json_logs(14) + "\n\n")
ATT_0091 = (NPM_NOTICE + "page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL\nCall log:\n"
            '  - navigating to "/admin/accounts", waiting until "load"\n\nServer diagnostic tail:\n' + NEXT_BANNERS + json_logs(8))
ATT_0088 = (NPM_NOTICE + "next build must succeed with a secret-free environment and isolated HOME.\n> demo@0.1.0 build\n"
            "> next build\n\n▲ Next.js 16.3.0 (Turbopack)\n  Creating an optimized production build ...\n"
            "✓ Compiled successfully in 21.8s\n  Running TypeScript ...\n\n\n<--- Last few GCs --->\n\n"
            "[228:0x3e6cc000]    51265 ms: Mark-Compact 2040.0 (2050.7) -> 2036.0 (2051.0) MB, pooled: 0 MB, 855.12 / 0.00 ms "
            " (average mu = 0.186, current mu = 0.025) allocation failure; scavenge might not succeed\n\n"
            "FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory\n"
            "----- Native stack trace -----\n\n"
            + "".join(f"{n:2d}: 0x{n:06x}  [/usr/local/bin/node]\n" for n in range(1, 11))
            + "Failed to type check.\n\n\n\n1 !== 0\n\nServer diagnostic tail:\n\n")
ATT_0093 = (NPM_NOTICE + "node:internal/modules/esm/resolve:272\n    throw new ERR_MODULE_NOT_FOUND(\n          ^\n\n"
            "Error [ERR_MODULE_NOT_FOUND]: Cannot find module '/workspace/scripts/test/test-glb-all-types.ts' imported from /workspace/\n"
            "    at finalizeResolution (node:internal/modules/esm/resolve:272:11)\n"
            "    at moduleResolve (node:internal/modules/esm/resolve:879:10)\n"
            "    at resolve (file:///workspace/node_modules/tsx/dist/register.mjs:2:15991) {\n"
            "  code: 'ERR_MODULE_NOT_FOUND',\n  url: 'file:///workspace/scripts/test/test-glb-all-types.ts'\n}\n\nNode.js v24.21.0\n")
MISSING_PACKAGE = (NPM_NOTICE + "Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'zod' imported from /workspace/lib/schema.ts\n"
                   "    at packageResolve (node:internal/modules/esm/resolve:767:9)\n")
DB_URL = (NPM_NOTICE + "Error: Set APP_TEST_DATABASE_URL, or set DATABASE_URL together with CI=true and APP_ENV=test.\n"
          "    at resolveTestDatabaseTarget (/workspace/scripts/test/lib/test-db.ts:25:11)\n"
          "    at main (/workspace/scripts/test/test-accounts-ui.ts:103:18)\n")
PYTEST = ("============================= test session starts ==============================\ncollected 120 items\n\n"
          "tests/test_quote.py F" + "." * 60 + " [ 50%]\n\n=================================== FAILURES ===================================\n"
          "_______________________________ test_quote_total _______________________________\n\n    def test_quote_total():\n"
          ">       assert quote_total(3) == 4\nE       assert 3 == 4\nE        +  where 3 = quote_total(3)\n\n"
          "tests/test_quote.py:12: AssertionError\n------------------------------ Captured log call -------------------------------\n"
          + "".join(f"INFO     app.quote:quote.py:40 computing line {n} of the quote for the customer table\n" for n in range(40))
          + "=========================== short test summary info ============================\n"
          "FAILED tests/test_quote.py::test_quote_total - assert 3 == 4\n========================= 1 failed, 119 passed in 3.21s ====\n")
UNITTEST = ("test_a (tests.test_quote.Quote.test_a) ... ok\nFAIL: test_total (tests.test_quote.Quote.test_total)\n"
            "----------------------------------------------------------------------\nTraceback (most recent call last):\n"
            '  File "/workspace/tests/test_quote.py", line 12, in test_total\n    self.assertEqual(total(3), 4)\n'
            "AssertionError: 3 != 4\n\n----------------------------------------------------------------------\n"
            "Ran 120 tests in 2.000s\n\nFAILED (failures=1)\n")
APP_PRINTS = "".join(f"seeded customer {n} with 3 quotes and 2 invoices for the demo tenant\n" for n in range(40))

DEPENDENCY_ADVICE = "Install the locked dependencies"
SOURCE_ADVICE = "a source file the check imports does not exist"


def port(artifacts, paths=()):
    plan = SimpleNamespace(tasks=[SimpleNamespace(id="T1", expected_paths=tuple(paths))])
    return SimpleNamespace(store=SimpleNamespace(get_artifact=lambda ref: artifacts.get(ref)), core=SimpleNamespace(plan=plan))


def digest(stderr: str, stdout: str = "", command: str = "npm run accounts:test-ui", code: int = 1, paths=()) -> str:
    artifacts = {"err": stderr.encode(), "out": stdout.encode()}
    check = {"command": command, "status": "fail", "exit_code": code, "stderr_ref": "err", "stdout_ref": "out"}
    return QualityVerificationPort._failure_digest(port(artifacts, paths), {"checks": [check]})


class DecisiveLineSurvives(unittest.TestCase):
    def test_att_0095_the_playwright_timeout_buried_under_json_logs_reaches_the_note(self):
        self.assertGreater(len(ATT_0095.split("exceeded.")[1]), 1500)            # the fixture really buries it
        note = digest(ATT_0095, BUILD_BANNERS)
        self.assertIn("locator.waitFor: Timeout 30000ms exceeded.", note)
        self.assertIn("waiting for getByRole('heading', { name: 'Enlace de invitación', exact: true })", note)
        json_chars = sum(len(line) for line in note.splitlines() if line.lstrip().startswith('{"'))
        self.assertLess(json_chars, len(note) // 4, "JSON info logs must not dominate the note")
        self.assertLess(note.index("locator.waitFor"), note.index("Types generated successfully"))

    def test_att_0091_the_invalid_url_keeps_its_call_log(self):
        note = digest(ATT_0091, BUILD_BANNERS)
        self.assertIn("page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL", note)
        self.assertIn('navigating to "/admin/accounts", waiting until "load"', note)

    def test_uvs_hardlink_warning_is_never_the_decisive_line(self):
        """D-236: pictures REQ-021 T10.45 a2/a3 — the agent was told uv's warning instead of the snapshot mismatch."""
        out = ("warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.\n"
               "         If the cache and target directories are on different filesystems, hardlinking may not be supported.\n"
               "         If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.\n"
               "INFO:     127.0.0.1:5000 - GET /healthz 200\n"
               "CG-10: candidate_identity_failure: snapshot source bytes match: .evidence/REQ-021/SP-10.integration.json\n"
               "+ actual - expected\n\n+ 'bcee9ac5'\n- '9a380a32'\n")
        from bitacora_platform import failure_lines
        got = failure_lines.decisive_excerpt(out)
        self.assertNotIn("hardlink", got)
        self.assertIn("candidate_identity_failure", got)
        self.assertIn("+ actual - expected", got)

    def test_a_short_output_still_gets_its_decisive_section(self):
        note = digest(DB_URL)
        self.assertIn("Decisive lines", note)
        self.assertIn("Error: Set APP_TEST_DATABASE_URL", note)
        self.assertIn("at resolveTestDatabaseTarget", note)                       # its first stack frame

    def test_pytest_assertion_detail_survives_the_captured_logs(self):
        note = digest(PYTEST, command="uv run pytest -q")
        self.assertIn("where 3 = quote_total(3)", note)
        self.assertIn("FAILED tests/test_quote.py::test_quote_total", note)

    def test_unittest_failure_survives_what_the_app_printed_after_it(self):
        note = digest(UNITTEST, APP_PRINTS, command="python3 -m unittest")
        self.assertIn("FAIL: test_total (tests.test_quote.Quote.test_total)", note)
        self.assertIn("AssertionError: 3 != 4", note)

    def test_json_error_logs_are_decisive_and_info_logs_are_not(self):
        error = json.dumps({"ts": "2026-10-28T19:41:10Z", "nivel": "error", "evento": "db.connect", "mensaje": "pool exhausted"})
        note = digest(NPM_NOTICE + json_logs(10) + error + "\n" + json_logs(10), BUILD_BANNERS)
        self.assertIn('"mensaje": "pool exhausted"', note)

    def test_the_note_stays_bounded_for_three_huge_failing_checks(self):
        noisy = "".join(f"Error: request {n} failed with a long explanation of what went wrong in module {n}\n"
                        for n in range(400)) + json_logs(200)
        artifacts = {"err": noisy.encode(), "out": noisy.encode()}
        checks = [{"command": f"npm run check:{n}", "status": "fail", "exit_code": 1, "stderr_ref": "err", "stdout_ref": "out"}
                  for n in range(3)]
        note = QualityVerificationPort._failure_digest(port(artifacts), {"checks": checks})
        self.assertLess(len(note), 12000)
        self.assertIn("Error: request 0 failed", note)                            # the first failure, not only the last


class Hints(unittest.TestCase):
    def test_att_0093_a_missing_source_file_is_not_called_a_dependency_problem(self):
        note = digest(ATT_0093, BUILD_BANNERS, command="npx tsx scripts/test/test-glb-all-types.ts")
        self.assertIn(SOURCE_ADVICE, note)
        self.assertIn("/workspace/scripts/test/test-glb-all-types.ts", note)
        self.assertNotIn(DEPENDENCY_ADVICE, note)
        self.assertNotIn("npm ci --offline", note)

    def test_a_missing_package_keeps_the_dependency_advice(self):
        note = digest(MISSING_PACKAGE)
        self.assertIn(DEPENDENCY_ADVICE, note)
        self.assertIn("npm ci --offline", note)
        self.assertNotIn(SOURCE_ADVICE, note)

    def test_relative_typescript_and_in_repo_python_modules_are_source_files(self):
        ts = digest("src/app.ts(3,20): error TS2307: Cannot find module './lib/missing' or its corresponding type declarations.\n",
                    command="npx tsc --noEmit")
        self.assertIn(SOURCE_ADVICE, ts)
        self.assertNotIn(DEPENDENCY_ADVICE, ts)
        py = digest("ModuleNotFoundError: No module named 'app.services'\n", command="python3 -m unittest",
                    paths=("app/services/__init__.py",))
        self.assertIn(SOURCE_ADVICE, py)
        self.assertNotIn(DEPENDENCY_ADVICE, py)
        third_party = digest("ModuleNotFoundError: No module named 'requests'\n", command="python3 -m unittest",
                             paths=("app/services/__init__.py",))
        self.assertIn(DEPENDENCY_ADVICE, third_party)

    def test_an_unnamed_missing_module_gets_advice_for_both_cases(self):
        note = digest("Error: MODULE_NOT_FOUND while loading the reporter\n")
        self.assertIn("if it is a file of the repository", note)
        self.assertNotIn(SOURCE_ADVICE, note)

    def test_att_0088_node_heap_exhaustion_is_named_an_environment_limit(self):
        note = digest(ATT_0088, BUILD_BANNERS)
        self.assertIn("FATAL ERROR: Ineffective mark-compacts near heap limit", note)
        self.assertIn("sandbox", note.split("$ ")[0])
        self.assertIn("NODE_OPTIONS=--max-old-space-size", note)
        self.assertIn("do not change product code", note.lower())
        self.assertNotIn(DEPENDENCY_ADVICE, note)

    def test_no_memory_hint_without_memory_evidence(self):
        self.assertNotIn("NODE_OPTIONS", digest(DB_URL))


class Extractor(unittest.TestCase):
    def test_patterns_the_old_error_regex_missed(self):
        from bitacora_platform import failure_lines

        text = ("noise\n" * 5 + "TypeError: x.map is not a function\n" + "noise\n" * 5 + "page.waitForURL: Timeout 20000ms exceeded.\n"
                "=========================== logs ===========================\nwaiting for navigation until \"load\"\n"
                "  navigated to \"http://127.0.0.1:39005/login?error=auth-unavailable\"\n" + "noise\n" * 5
                + "A system error occurred: uv_os_homedir returned ENOENT (no such file or directory)\n"
                + "  1) [chromium] › tests/login.spec.ts:12:5 › logs in\n" + "Segmentation fault (core dumped)\n")
        excerpt = failure_lines.decisive_excerpt(text)
        for needle in ("TypeError: x.map is not a function", "page.waitForURL: Timeout 20000ms exceeded.",
                       "navigated to \"http://127.0.0.1:39005/login?error=auth-unavailable\"", "uv_os_homedir returned ENOENT",
                       "[chromium] › tests/login.spec.ts:12:5", "Segmentation fault"):
            self.assertIn(needle, excerpt)
        self.assertNotIn("noise", excerpt)

    def test_lines_are_deduplicated_ordered_and_bounded(self):
        from bitacora_platform import failure_lines

        text = "Error: first\n" + "Error: same\n" * 50 + "".join(f"Error: n{n} " + "x" * 150 + "\n" for n in range(100))
        excerpt = failure_lines.decisive_excerpt(text, limit=900)
        self.assertLessEqual(len(excerpt), 900)
        self.assertEqual(excerpt.count("Error: same"), 1)
        self.assertLess(excerpt.index("Error: first"), excerpt.index("Error: same"))

    def test_module_kinds(self):
        from bitacora_platform import failure_lines

        cases = {"react": "package", "@scope/pkg": "package", "@scope/pkg/sub": "package", "chart.js": "package",
                 "./lib/x": "source", "../x": "source", "/workspace/scripts/test/x.ts": "source", "@/lib/db": "source",
                 "scripts/test/x.ts": "source", "file:///workspace/x.ts": "source", "#internal/db": "source",
                 "/workspace/node_modules/left-pad/index.js": "package", "requests": "package"}
        for name, kind in cases.items():
            with self.subTest(name=name):
                self.assertEqual(failure_lines.module_kind(name), kind)
        self.assertEqual(failure_lines.module_kind("app.services", ("app/services/__init__.py",)), "source")
        self.assertEqual(failure_lines.module_kind("app", ("app/main.py",)), "source")

    def test_clip_keeps_a_decisive_line_from_the_part_it_cuts(self):
        from bitacora_platform import failure_lines

        text = "header line\n" + "progress ok\n" * 300 + "locator.click: Timeout 5000ms exceeded.\n" + "progress ok\n" * 50
        clipped = failure_lines.clip(text, 600)
        self.assertLessEqual(len(clipped), 600)
        self.assertIn("locator.click: Timeout 5000ms exceeded.", clipped)
        self.assertTrue(clipped.startswith("header line"))
        tail = failure_lines.clip(text, 600, keep="tail")
        self.assertLessEqual(len(tail), 600)
        self.assertIn("locator.click: Timeout 5000ms exceeded.", tail)
        self.assertEqual(failure_lines.clip("short", 600), "short")


class OtherReaders(unittest.TestCase):
    """The builders that summarize the note for the owner, the diagnosis and the self-healing keep the decisive line too."""

    def note(self):
        return digest(ATT_0095, BUILD_BANNERS)

    def test_the_history_excerpt_quotes_the_failure_not_the_preamble(self):
        import bt_attempt_history as history

        excerpt = history._excerpt(self.note())
        self.assertIn("locator.waitFor: Timeout 30000ms exceeded.", excerpt)

    def test_the_repair_excerpt_keeps_the_playwright_line(self):
        import bt_prompt_context

        with patch.object(bt_prompt_context, "concise", lambda: False):
            excerpt = bt_prompt_context.repair_excerpt(self.note())
        self.assertIn("locator.waitFor: Timeout 30000ms exceeded.", excerpt)

    def test_the_owner_card_keeps_a_decisive_line_beyond_its_clip(self):
        import bt_scheduler_decisions as decisions

        text = "Last failure:\n" + "progress ok\n" * 200 + "page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL\n"
        self.assertIn("page.goto: Protocol error", decisions._clip(text))

    def test_the_provider_error_excerpt_recognises_a_timeout(self):
        import bt_events

        self.assertEqual(bt_events.error_excerpt("working...\nlocator.waitFor: Timeout 30000ms exceeded.\ndone\n"),
                         "locator.waitFor: Timeout 30000ms exceeded.")

    def test_the_diagnosis_bundle_keeps_the_decisive_line_of_a_long_note(self):
        import bt_block_diagnosis as rules

        verify = "$ npm test\nexit code 1\n" + "progress ok\n" * 400 + "locator.waitFor: Timeout 30000ms exceeded.\n"
        failure = "verification rejected: " + "x " * 300 + "AssertionError: 3 != 4"
        text = rules.bundle({"id": "T1:2", "task": "T1"}, verify=verify, failures=[failure])
        self.assertIn("locator.waitFor: Timeout 30000ms exceeded.", text)
        self.assertIn("AssertionError: 3 != 4", text)

    def test_a_missing_source_file_is_diagnosed_as_code_and_not_healed_as_environment(self):
        import bt_block_diagnosis as rules
        import bt_healing_classify as taxonomy

        verify = digest(ATT_0093, command="npx tsx scripts/test/test-glb-all-types.ts")
        request = {"id": "T3.11:4", "task": "T3.11", "source": "task", "reason": "m5:attempts_exhausted", "error": "",
                   "options": [{"id": "retry"}, {"id": "retry_with_note"}, {"id": "stop"}]}
        diagnosis, _ = rules.explain(request, {}, verify=verify)
        self.assertNotEqual(diagnosis["kind"], "dependency")
        self.assertNotIn("package.json", diagnosis["note"])
        self.assertIn("/workspace/scripts/test/test-glb-all-types.ts", diagnosis["headline"] + diagnosis["origin"])
        case = taxonomy.classify({**request, "diagnosis": diagnosis}, verify=verify)
        self.assertTrue(case is None or case.kind != "environment", case)
        # a "dependency" card cached before the split (or a model's guess) does not route the source file to environment
        stale = taxonomy.classify({**request, "diagnosis": {"kind": "dependency", "headline": "Falta la dependencia x"}},
                                  verify=verify)
        self.assertTrue(stale is None or stale.kind != "environment", stale)

    def test_a_missing_package_is_still_a_dependency_and_an_environment_case(self):
        import bt_block_diagnosis as rules
        import bt_healing_classify as taxonomy

        verify = digest(MISSING_PACKAGE)
        request = {"id": "T1:2", "task": "T1", "source": "task", "reason": "m5:attempts_exhausted", "error": "",
                   "options": [{"id": "retry"}, {"id": "retry_with_note"}, {"id": "stop"}]}
        diagnosis, _ = rules.explain(request, {}, verify=verify)
        self.assertEqual(diagnosis["kind"], "dependency")
        self.assertIn("zod", diagnosis["headline"])
        self.assertEqual(taxonomy.classify({**request, "diagnosis": diagnosis}, verify=verify).kind, "environment")


if __name__ == "__main__":
    unittest.main()
