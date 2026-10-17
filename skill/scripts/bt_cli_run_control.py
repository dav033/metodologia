"""Authority-aware CLI control for existing run supervisors."""
from __future__ import annotations

from pathlib import Path

import bt_scheduler_adapter as scheduler


def dispatch(rdir: Path, action: str) -> str:
    if not scheduler.scheduler_authority(rdir):
        import bt_runtask

        return bt_runtask.run_control(rdir, action)
    scheduler.apply_control(rdir, action, by="cli")
    return {"pause": "Ejecución Scheduler pausada.", "resume": "Ejecución Scheduler reanudada.",
            "stop": "Cancelación enviada a M1."}[action]
