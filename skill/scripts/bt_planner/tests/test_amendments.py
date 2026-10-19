"""Amendments: classification changes during a run, append-only, never touching the approved plan."""
from __future__ import annotations

import datetime as dt
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bt_planner import amendments as am
from bt_planner import cli
from bt_planner import revisions as rev
from support import PlanDir

NOW = dt.datetime(2026, 10, 18, 22, 0, tzinfo=dt.UTC)


class Amend(PlanDir):
    def freeze(self):
        self.good()
        self.sync.approve_freeze(self.rdir, "REQ-042", ("approved",), None)

    def agent(self, field="complexity", to="high", **kw):
        kw.setdefault("evidence", ["file:src/auth/x.py"])
        return am.append(self.rdir, "T1", field, to, reason="the module is larger than estimated", by="claude",
                         proposed_by="agent", now=NOW, **kw)

    def test_agent_raises_with_evidence_and_the_effective_value_follows(self):
        self.freeze()
        record = self.agent()
        self.assertEqual((record["seq"], record["from"], record["to"], record["at"]), (1, "low", "high", "2026-10-18T22:00:00+00:00"))
        plan = rev.load_revision(self.rdir, 1)
        self.assertEqual(am.effective(plan, am.read(self.rdir))["T1"]["complexity"], "high")
        self.assertEqual(am.effective(plan, am.read(self.rdir))["T2"]["complexity"], "low")   # other tasks untouched
        self.assertEqual(plan["tasks"][0]["complexity"], "low")                               # the frozen plan never changes

    def test_the_frozen_revision_and_plan_json_are_untouched(self):
        self.freeze()
        before = {p.name: p.read_bytes() for p in [self.rdir / "PLAN.json", rev.revision_path(self.rdir, 1)]}
        self.agent()
        self.assertEqual(before, {p.name: p.read_bytes() for p in [self.rdir / "PLAN.json", rev.revision_path(self.rdir, 1)]})

    def test_an_agent_cannot_lower_but_the_owner_can(self):
        self.freeze()
        self.agent(to="high")
        with self.assertRaises(am.AmendmentError) as ctx:
            am.append(self.rdir, "T1", "complexity", "medium", reason="seems easier", by="claude",
                      proposed_by="agent", evidence=["x"], now=NOW)
        self.assertEqual(ctx.exception.code, "AMEND_LOWER_NEEDS_OWNER")
        record = am.append(self.rdir, "T1", "complexity", "medium", reason="owner call", by="david",
                           proposed_by="owner", now=NOW)
        self.assertEqual((record["seq"], record["from"], record["to"]), (2, "high", "medium"))

    def test_confidence_reads_the_other_way_round(self):
        self.freeze()
        self.assertEqual(am.direction("confidence", "medium", "low"), "raise")      # less confident = riskier
        self.assertEqual(am.direction("risk", "medium", "low"), "lower")
        self.assertEqual(am.direction("estimated_minutes", 30, 60), "raise")
        self.assertEqual(am.direction("scope", "small_change", "large_change"), "raise")

    def test_refusals_have_stable_codes(self):
        self.freeze()
        cases = [({"field": "model", "to": "x"}, "AMEND_FIELD"), ({"field": "complexity", "to": "huge"}, "AMEND_VALUE"),
                 ({"field": "complexity", "to": "low"}, "AMEND_NOOP"), ({"field": "estimated_minutes", "to": 0}, "AMEND_VALUE"),
                 ({"field": "complexity", "to": "high", "evidence": []}, "AMEND_EVIDENCE"),
                 ({"field": "complexity", "to": "high", "reason": "  "}, "AMEND_REASON"),
                 ({"field": "complexity", "to": "high", "task": "T99"}, "AMEND_TASK"),
                 ({"field": "complexity", "to": "high", "proposed_by": "robot"}, "AMEND_AUTHOR")]
        for extra, code in cases:
            args = {"task": "T1", "field": "complexity", "to": "high", "reason": "r", "evidence": ["e"], "by": "me",
                    "proposed_by": "agent", "now": NOW, **extra}
            with self.assertRaises(am.AmendmentError, msg=code) as ctx:
                am.append(self.rdir, args.pop("task"), args.pop("field"), args.pop("to"), **args)
            self.assertEqual(ctx.exception.code, code)
        self.assertEqual(am.read(self.rdir), [])

    def test_a_stale_from_is_ignored_and_junk_lines_are_skipped(self):
        self.freeze()
        self.agent()
        path = am.path_of(self.rdir)
        stale = {**am.read(self.rdir)[0], "seq": 2, "from": "low", "to": "extreme"}   # `from` no longer matches
        path.write_text(path.read_text() + "not json\n" + json.dumps(stale) + "\n" + json.dumps({"seq": 3}) + "\n")
        plan = rev.load_revision(self.rdir, 1)
        self.assertEqual([r["seq"] for r in am.read(self.rdir)], [1, 2])
        self.assertEqual(am.effective(plan, am.read(self.rdir))["T1"]["complexity"], "high")

    def test_amendments_bound_to_an_older_revision_do_not_apply_to_a_newer_one(self):
        self.freeze()
        self.agent()
        newer = json.loads(json.dumps(rev.load_revision(self.rdir, 1)))
        newer["revision"] = 2
        self.assertEqual(am.effective(newer, am.read(self.rdir))["T1"]["complexity"], "low")
        self.assertEqual(am.history(newer, am.read(self.rdir), "T1"), [])

    def test_append_without_a_plan_is_refused(self):
        with self.assertRaises(am.AmendmentError) as ctx:
            self.agent()
        self.assertEqual(ctx.exception.code, "AMEND_NO_PLAN")

    def test_concurrent_appends_keep_a_gapless_sequence(self):
        import threading
        self.freeze()
        errors = []

        def worker(minutes):
            try:
                am.append(self.rdir, "T2", "estimated_minutes", minutes, reason="r", evidence=["e"], by="a",
                          proposed_by="agent", now=NOW)
            except am.AmendmentError as exc:
                errors.append(exc.code)

        threads = [threading.Thread(target=worker, args=(60 + i,)) for i in range(6)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual([r["seq"] for r in am.read(self.rdir)], list(range(1, len(am.read(self.rdir)) + 1)))
        self.assertEqual(len(am.read(self.rdir)) + len(errors), 6)

    def test_cli_amend_and_list(self):
        self.freeze()
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli.main(["amend", str(self.rdir), "--task", "T1", "--field", "complexity", "--to", "high",
                             "--reason", "bigger than thought", "--evidence", "file:a", "--by", "claude",
                             "--proposed-by", "agent"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("low → high", out.getvalue())
        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(["amendments", str(self.rdir)])
        self.assertEqual(json.loads(out.getvalue())[0]["to"], "high")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["amend", str(self.rdir)]), 2)


if __name__ == "__main__":
    unittest.main()


class Robustness(PlanDir):
    def test_an_oversized_line_stops_the_read_without_buffering_it(self):
        self.good()
        self.sync.approve_freeze(self.rdir, "REQ-042", ("approved",), None)
        am.append(self.rdir, "T1", "complexity", "high", reason="r", evidence=["e"], by="a", proposed_by="agent", now=NOW)
        with am.path_of(self.rdir).open("a", encoding="utf-8") as handle:
            handle.write("x" * (am.MAX_LINE + 10) + "\n")
        self.assertEqual([r["seq"] for r in am.read(self.rdir)], [1])

    def test_the_plan_revision_is_read_under_the_freeze_lock(self):
        """An amendment bound to r1 cannot be written once r2 is frozen: the freeze lock is held while reading."""
        import threading
        from bt_planner._lock import exclusive
        self.good()
        self.sync.approve_freeze(self.rdir, "REQ-042", ("approved",), None)
        held, release, result = threading.Event(), threading.Event(), {}

        def freezer():
            with exclusive(self.rdir / rev.DIR / rev.LOCK_NAME):
                held.set()
                release.wait(5)

        thread = threading.Thread(target=freezer)
        thread.start()
        held.wait(5)

        def amender():
            result["record"] = am.append(self.rdir, "T1", "complexity", "high", reason="r", evidence=["e"], by="a",
                                         proposed_by="agent", now=NOW)

        worker = threading.Thread(target=amender)
        worker.start()
        worker.join(0.3)
        self.assertTrue(worker.is_alive(), "the amendment must wait for the freeze lock")
        release.set()
        thread.join()
        worker.join(5)
        self.assertEqual(result["record"]["plan_ref"]["revision"], 1)
