"""A tiny engine process for scenario I (REQ-030 M9): the same workflow in two code versions.

`python durable_version_probe.py <db url> <out dir> <v1|v2> [start <workflow id>]`. v2 adds a step behind
`DBOS.patch("extra-step")`, the upgrade procedure bt_durable uses (engine.py, README "Upgrading workflows").
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from dbos import DBOS, SetWorkflowID

URL, OUT, VERSION = sys.argv[1], Path(sys.argv[2]), sys.argv[3]


def mark(name: str) -> None:
    with open(OUT / "trace.jsonl", "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"step": name, "version": VERSION, "workflow": DBOS.workflow_id}) + "\n")


@DBOS.step()
def step_a() -> None:
    mark("a")


@DBOS.step()
def step_extra() -> None:
    mark("extra")


@DBOS.step()
def step_b() -> None:
    mark("b")


@DBOS.step()
def step_c() -> None:
    mark("c")


@DBOS.workflow(name="probe.versioned")
def versioned() -> str:
    """The patch sits right before a plain step (`step_b`), never right before a durable wait: a workflow blocked in
    a recv/sleep that the patch would precede has no checkpoint at that position yet, DBOS would take the patch for
    it, and the step after it would land where the wait's own records are (DBOSUnexpectedStepError)."""
    step_a()
    DBOS.recv("go1", timeout_seconds=300)
    if VERSION == "v2" and DBOS.patch("extra-step"):
        step_extra()
    step_b()
    DBOS.recv("go2", timeout_seconds=300)
    step_c()
    return VERSION


DBOS(config={"name": "bt-version-probe", "system_database_url": URL, "enable_patching": True})
DBOS.launch()
if len(sys.argv) > 5 and sys.argv[4] == "start":
    with SetWorkflowID(sys.argv[5]):
        DBOS.start_workflow(versioned)
(OUT / f"ready-{VERSION}").write_text("1")
while True:
    time.sleep(0.5)
