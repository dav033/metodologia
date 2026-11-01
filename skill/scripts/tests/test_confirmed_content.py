"""D-276: a subplan whose draft returns to content already confirmed in that exact form is confirmed again, by policy.

pictures REQ-021 (2026-10-31): D-241 re-confirmed SP-3 by policy for the Solucionador's repair T3.121 (stage r33); the
owner chose «Retirar T3.121», the Planner removed it and SP-3 was byte-identical to its r31/r32 content (confirmed by
D-241 at 16:02), yet the stage freeze refused «SP-3: cambió después de confirmarlo; vuelve a confirmarlo».
"""
from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_cli_planning
import bt_confirmed_content as cc
import bt_planning_activity as activity
import bt_planning_flow as flow
import bt_planning_notes as notes
import bt_stages
import bt_subplan_status
import test_bounded_repair as tbr

planner = tbr.planner
EVIDENCE = ["RUN.notes/T2.verify.md"]


class ConfirmedContent(unittest.TestCase):
    setUp = tbr.StageFreeze.setUp
    draft = tbr.StageFreeze.draft
    plan = tbr.StageFreeze.plan

    def repaired(self) -> dict:
        """Owner-confirmed X frozen in r1; the D-241 repair X+T1.1 frozen by policy in r2. Returns X."""
        original = self.plan()
        self.draft(tbr.with_repair(original))
        self.repair = bt_stages.freeze("proj", self.rdir, [], repair_evidence=EVIDENCE, by="solver")
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-1"]["policy"]["rule"], "D-241")
        return original

    def sp1(self) -> dict:
        return flow.state(self.rdir)["subplans"]["SP-1"]

    def record(self) -> dict:
        return flow._load(self.rdir)["subplans"]["SP-1"]

    def refused(self) -> bt_stages.StageError:
        with self.assertRaises(bt_stages.StageError) as ctx:
            bt_stages.freeze("proj", self.rdir, [])
        self.assertEqual(ctx.exception.code, "STAGE_SUBPLAN_UNCONFIRMED")
        return ctx.exception

    def test_withdrawing_a_policy_repair_freezes_without_the_owner_and_says_why(self):
        original = self.repaired()
        self.draft(original)
        self.assertEqual(self.sp1()["state"], "changed")
        entry = bt_stages.freeze("proj", self.rdir, [])                 # no owner action, no evidence
        self.assertEqual(entry["revision"], self.repair["revision"] + 1)
        self.assertNotIn("T1.1", tbr.tasks(planner.load_revision(self.rdir, entry["revision"])))
        record = self.record()
        self.assertEqual((record["by"], record["via"], record["policy"]["rule"], record["policy"]["restores"]["by"]),
                         ("policy", "policy", "D-276", "owner"))
        self.assertRegex(record["policy"]["reason"],
                         r"^vuelve al contenido confirmado el \d{4}-\d\d-\d\d \d\d:\d\d por el propietario$")
        self.assertEqual(record["policy"]["previous"]["digest"], record["history"][-1]["digest"])
        self.assertEqual([h["by"] for h in record["history"]], ["owner", "policy"])   # the D-241 record is kept
        self.assertEqual(record["history"][1]["policy"]["previous"]["digest"], record["digest"])
        self.assertEqual(self.sp1()["state"], "confirmed")
        said = [e for e in activity.events(self.rdir) if e["who"] == "Política" and "D-276" in e["text"]]
        self.assertTrue(said and "por el propietario" in said[-1]["text"], said)
        self.assertTrue(any(n["by"] == "policy" and "D-276" in n["text"] for n in notes.notes(self.rdir)))
        shown = bt_subplan_status.status({"flow": flow.state(self.rdir), "rows": {}}, {"id": "SP-1", "ref": None, "tasks": [1]},
                                         {"rounds": (None, []), "inputs": {}, "tasks": {}, "held": ["SP-1"], "queued": {},
                                          "decided": set(), "decisions": [], "gates": {}, "verified": {}, "events": []})
        self.assertTrue(any("regla D-276" in d["text"] and "por el propietario" in d["text"]
                            for d in shown["decisions"]), shown["decisions"])
        self.assertEqual(cc.restore(self.rdir), [])                          # idempotent

    def test_any_other_change_still_waits_for_the_owner(self):
        original = self.repaired()
        other = json.loads(json.dumps(original))
        tbr.tasks(other)["T2"]["title"] = "Something the owner never saw"
        self.draft(other)
        self.assertIn("SP-1: cambió después de confirmarlo", self.refused().message)
        self.assertEqual((self.sp1()["state"], cc.restore(self.rdir)), ("changed", []))
        self.draft(original)                         # the confirmed plan, but its `## Pruebas` row changed since
        spec = (self.rdir / "SPEC.md").read_text()
        (self.rdir / "SPEC.md").write_text(spec.replace("| one works |", "| anything |"))
        self.refused()
        self.assertEqual(self.record()["policy"]["rule"], "D-241")

    def test_content_the_owner_rejected_is_never_restored(self):
        original = self.repaired()
        repaired = self.plan()
        self.assertIn("rechazado", cc.reject(self.rdir, "SP-1", why="T1.1 es redundante"))
        self.assertEqual(self.sp1()["state"], "changed")                    # the rejected repair needs the owner
        self.refused()
        self.draft(original)                                                # the Planner withdraws it
        self.assertEqual(cc.restore(self.rdir), ["SP-1"])
        self.assertEqual(self.record()["policy"]["restores"]["by"], "owner")
        self.draft(repaired)                                                # the rejected content comes back
        self.assertEqual(cc.restore(self.rdir), [])
        self.refused()
        flow.confirm("proj", self.rdir, "SP-1")                             # only the owner confirms it anew
        self.assertEqual((self.sp1()["state"], self.record()["by"]), ("confirmed", "owner"))

    def test_back_to_an_earlier_owner_confirmation_outside_a_repair(self):
        original = self.plan()
        changed = json.loads(json.dumps(original))
        tbr.tasks(changed)["T2"]["title"] = "Renamed by the Planner"
        self.draft(changed)
        flow.confirm("proj", self.rdir, "SP-1")
        self.draft(original)                                                # back to what the owner confirmed first
        self.assertEqual(bt_stages.freeze("proj", self.rdir, [])["revision"], self.first["revision"])
        self.assertEqual([h["by"] for h in self.record()["history"]], ["owner", "owner"])
        self.assertEqual(self.record()["policy"]["rule"], "D-276")

    def test_a_legacy_d241_record_proves_the_confirmation_it_replaced(self):
        original = self.repaired()

        def legacy() -> None:                                                # flow.json as written before D-276
            path = self.rdir / flow.DIR / flow.FILE
            data = json.loads(path.read_text())
            record = data["subplans"]["SP-1"]
            record.pop("history")
            record["policy"]["previous"].pop("digest")
            path.write_text(json.dumps(data))
        legacy()
        self.draft(original)
        bt_stages.freeze("proj", self.rdir, [])
        record = self.record()
        self.assertEqual(record["policy"]["restores"]["by"], "owner")
        self.assertIn(f"r{self.first['revision']}", record["history"][0]["derived"])
        self.assertEqual(record["history"][0]["digest"], record["digest"])

    def test_a_legacy_record_derives_nothing_once_the_tests_changed(self):
        original = self.repaired()
        path = self.rdir / flow.DIR / flow.FILE
        data = json.loads(path.read_text())
        data["subplans"]["SP-1"].pop("history")
        data["subplans"]["SP-1"]["policy"]["previous"].pop("digest")
        path.write_text(json.dumps(data))
        self.draft(original)
        spec = (self.rdir / "SPEC.md").read_text()
        (self.rdir / "SPEC.md").write_text(spec.replace("| one works |", "| anything |"))
        self.assertEqual(cc.restorable(self.rdir), {})
        self.refused()

    def test_reject_records_only_the_owner_word(self):
        args = argparse.Namespace(action="reject", req="REQ-900", subplan="SP-1", by=None, text="no", kind="finding")
        with patch.object(bt_cli_planning, "find_req", return_value=self.rdir):
            with self.assertRaises(SystemExit) as ctx:
                bt_cli_planning.dispatch(args, self.rdir.parent, "proj")
            self.assertIn("--by owner", str(ctx.exception))
            self.assertEqual(self.sp1()["state"], "confirmed")
            args.by = "owner"
            bt_cli_planning.dispatch(args, self.rdir.parent, "proj")
        self.assertEqual((self.sp1()["state"], self.record()["rejected"]["reason"]), ("changed", "no"))

if __name__ == "__main__":
    unittest.main()
