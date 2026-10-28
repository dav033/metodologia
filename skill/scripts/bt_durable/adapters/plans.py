"""PlanSource port over frozen plan files: the bytes are hash-checked before anything reads them."""
from __future__ import annotations

import hashlib

from bt_contracts.execution import RunRef

from ..legacy import Plan, load_plan


class FilePlans:
    def text(self, run: RunRef) -> str:
        data = run.plan_path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != run.plan_sha256:
            raise RuntimeError(f"PLAN_CHANGED: {run.plan_path.name} is {digest[:12]}, approved {run.plan_sha256[:12]}")
        return data.decode("utf-8")

    def load(self, run: RunRef) -> Plan:
        return load_plan(self.text(run), approved_sha256=run.plan_sha256, plan_id=run.plan_id, revision=run.revision)
