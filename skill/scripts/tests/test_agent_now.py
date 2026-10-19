import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_agent_now as now

WT = "/home/x/.state/executor/p-REQ-1-r1-x/ws/worktrees/att-0007-abc"


def claude_log(*events) -> str:
    return "\n".join(json.dumps(e) for e in events) + "\n"


def tool_use(tid, name, **args):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": tid, "name": name, "input": args}]}}


def said(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def result(tid, error=False):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "is_error": error}]}}


class Parse(unittest.TestCase):
    def test_claude_current_tool_last_sentence_and_finished_steps(self):
        text = claude_log(said("Leo el test."), tool_use("a", "Read", file_path=f"{WT}/src/a.ts"), result("a"),
                          tool_use("b", "Bash", command=f"cd {WT} && npm test"), result("b", error=True),
                          said("Falla un caso; lo corrijo."), tool_use("c", "Bash", command="npm run gate"))
        out = now._claude(text)
        self.assertEqual(out["current"], {"tool": "Bash", "what": "npm run gate"})
        self.assertEqual(out["said"], "Falla un caso; lo corrijo.")
        self.assertEqual([(s["tool"], s["what"], s["ok"]) for s in out["steps"]],
                         [("Read", "src/a.ts", True), ("Bash", "npm test", False)])   # worktree prefix and `cd` dropped

    def test_codex_text_blocks(self):
        text = "\n".join([
            "codex", "Corro el lint primero.", "exec", f"/usr/bin/bash -lc 'npx eslint src' in {WT}", "boom",
            " exited 1 in 5071ms:", "apply patch", "patch: completed", f"{WT}/src/b.ts", "diff --git a/src/b.ts b/src/b.ts",
            "codex", "Arreglado; vuelvo a correrlo.", "exec", f"/usr/bin/bash -lc 'npx eslint src' in {WT}", ""])
        out = now._codex(text)
        self.assertEqual(out["current"], {"tool": "exec", "what": "npx eslint src"})
        self.assertEqual(out["said"], "Arreglado; vuelvo a correrlo.")
        self.assertEqual([(s["tool"], s["what"], s["ok"]) for s in out["steps"]],
                         [("exec", "npx eslint src", False), ("apply patch", "src/b.ts", True)])

    def test_long_text_is_cut_and_garbage_yields_nothing(self):
        self.assertTrue(now._cut("x" * 1000, 50).endswith("…"))
        self.assertEqual(now._claude("not json\n{broken"), {"current": None, "said": None, "steps": []})


class Files(unittest.TestCase):
    def test_reads_the_newest_bytes_from_the_tail_file_once_the_log_head_is_full(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adir = root / ".state" / "executor" / "demo-REQ-001-r1-x" / "attempts" / "att-0007-abc"
            adir.mkdir(parents=True)
            (adir / "output.log").write_text(claude_log(said("viejo")))
            (adir / "output.tail").write_text(claude_log(said("nuevo"), tool_use("z", "Grep", pattern="TODO")))
            old = (adir / "output.log").stat().st_mtime - 30
            os.utime(adir / "output.log", (old, old))
            rdir = root / "demo" / "requirements" / "REQ-001-x"
            with patch.object(now.bt_run_stores, "paths", return_value={"m1": root / ".state" / "scheduler" / "x.db"}):
                found = now.now(rdir, "demo", ["att-0007", "att-0099"])
        self.assertEqual(list(found), ["att-0007"])
        self.assertEqual((found["att-0007"]["said"], found["att-0007"]["current"]["what"]), ("nuevo", "TODO"))


if __name__ == "__main__":
    unittest.main()
