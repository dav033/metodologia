"""Manual checks with coordinator receipts in the durable runtime (REQ-030 item 3), end to end with the real M6
sandbox, the real `bt_attestation` seal and the operator CLI (`bt-durable attest`) in its own process.

- No receipt: the task does not fail opaquely and no agent is relaunched — it opens a decision with its request id that
  names the manual check, the attempt a receipt must be bound to, and `reverify`; `bt-durable attest` seals the receipt
  and answers it, and the same snapshot passes. One agent launch in total.
- A valid receipt already there: the manual check passes without anyone being asked."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_contracts.execution import AttemptRef, RunRef
from durable_support import task, wait_until
from test_durable_e2e import FAST, EngineCase

MANUAL = {"type": "manual", "category": "product", "purpose": "The owner saw the lab page say good",
          "value": "Open the lab page in a browser and read its message", "expected": "the page says good"}


class DurableAttestations(EngineCase):
    def freeze(self, revision: int) -> RunRef:
        run = RunRef.model_validate(self.lab.freeze([task("T1", extra_checks=[MANUAL])], revision=revision))
        (self.lab.rdir / "RUN.owner.json").write_text(json.dumps({"backend": "dbos", "run_id": run.run_id,
                                                                  "workflow_id": f"bt:{run.run_id}"}))
        (self.lab.rdir / "RUN.durable-run.json").write_text(run.model_dump_json())
        return run

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, **self.lab.env(), "BT_DURABLE_DATABASE_URL": self.lab.database_url}
        return subprocess.run([sys.executable, "-m", "bt_durable", *args], env=env, capture_output=True, text=True,
                              timeout=120, check=False)

    def decision(self, run: RunRef) -> dict | None:
        return (self.client.status(run)["tasks"].get("T1") or {}).get("decision")

    def events(self, name: str) -> list[dict]:
        rows = [json.loads(line) for line in (self.lab.state / "telemetry.jsonl").read_text().splitlines()]
        return [row for row in rows if row.get("event") == name]

    def test_a_missing_receipt_is_a_decision_and_attesting_it_passes_the_same_snapshot(self):
        run = self.freeze(1)
        self.start_engine()
        self.client.start(run, FAST)
        decision = wait_until(lambda: self.decision(run), 240, interval=0.5, what="the manual-evidence decision")
        self.assertEqual(decision["request_id"], "T1:d1")
        self.assertEqual(decision["failure"]["code"], "MANUAL_EVIDENCE_REQUIRED", decision)
        self.assertIn(MANUAL["purpose"], decision["failure"]["summary"])
        self.assertEqual(decision["options"][0], "reverify")
        self.assertEqual(decision["verify_attempt"], AttemptRef(run=run, task_id="T1", number=1, workflow_id="x").attempt_key)
        self.assertIn("bt-durable attest", decision["attest"])

        stale = self.cli("attest", "proj", "REQ-900", "T1", "--request", "T1:d9", "--evidence",
                         "Opened the lab page and it said good in large letters.")
        self.assertNotEqual(stale.returncode, 0)                       # a stale request id writes nothing
        self.assertIn("STALE_REQUEST", stale.stderr + stale.stdout)
        self.assertFalse((self.lab.rdir / "RUN.attestations").exists())

        done = self.cli("attest", "proj", "REQ-900", "T1", "--request", "T1:d1", "--evidence",
                        "Opened the lab page and it said good in large letters.", "--by", "owner")
        self.assertEqual(done.returncode, 0, done.stderr)
        status = self.settled(run, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 1)                  # verified again, never re-run
        self.assertEqual([row["request_id"] for row in self.events("owner_reverify")], ["T1:d1"])

    def test_a_valid_receipt_settles_the_manual_check_without_asking(self):
        import bt_attestation
        run = self.freeze(1)
        attempt = AttemptRef(run=run, task_id="T1", number=1, workflow_id="x").attempt_key
        bt_attestation.mint(self.lab.rdir, "T1", MANUAL["purpose"], MANUAL["value"], MANUAL["expected"],
                            "Opened the lab page and it said good in large letters.", "owner", attempt=attempt,
                            key_file=self.lab.bitacora / ".state" / "attestation.key")
        self.start_engine()
        self.client.start(run, FAST)
        status = self.settled(run, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 1)
        self.assertEqual(self.events("decision_requested"), [])


if __name__ == "__main__":
    unittest.main()
