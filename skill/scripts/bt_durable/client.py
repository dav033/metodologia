"""Operator side of the durable runtime: start, observe and steer runs through the DBOS system database.

The engine service executes workflows; this client never does. It enqueues run workflows by name (with their
deterministic ID, so a repeated `start` returns the existing run), sends owner answers and run commands, reads the
`summary`/`state`/`decision` events, and cancels. Every message is validated against the owner contracts first.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterable

from dbos import DBOSClient, EnqueueOptions

from bt_contracts.execution import RunRef
from bt_contracts.owner import OwnerAnswer, RunCommand

from .execution.engine import APP_VERSION, RUNS
from .settings import Settings

RUN_WORKFLOW, TASK_WORKFLOW = "bt.run", "bt.task"


class Client:
    def __init__(self, system_database_url: str):
        self.client = DBOSClient(system_database_url=system_database_url)

    def close(self) -> None:
        self.client.destroy()

    # ----------------------------------------------------------------------------------------------- runs
    def start(self, run: RunRef, settings: Settings, inherited: dict[str, str] | None = None) -> str:
        workflow_id = f"bt:{run.run_id}"
        options: EnqueueOptions = {"workflow_name": RUN_WORKFLOW, "queue_name": RUNS, "workflow_id": workflow_id,
                                   "app_version": APP_VERSION}
        existing = self.client.list_workflows(workflow_ids=[workflow_id], load_input=False, load_output=False)
        if not existing:
            self.client.enqueue(options, run.model_dump(mode="json"), settings.model_dump(mode="json"),
                                dict(inherited or {}))
        return workflow_id

    def summary(self, run: RunRef) -> dict | None:
        return self.client.get_event(f"bt:{run.run_id}", "summary", timeout_seconds=0)

    def status(self, run: RunRef) -> dict:
        """The projection operators read: run summary plus each task workflow's state and open decision."""
        rows = self.client.list_workflows(workflow_id_prefix=f"bt:{run.run_id}", load_input=False, load_output=False)
        tasks = {}
        for row in rows:
            if row.name != TASK_WORKFLOW:
                continue
            task_id = row.workflow_id.rsplit(":", 2)[-2]
            tasks[task_id] = {"workflow_id": row.workflow_id, "workflow_status": row.status,
                              "state": self.client.get_event(row.workflow_id, "state", timeout_seconds=0),
                              "decision": self.client.get_event(row.workflow_id, "decision", timeout_seconds=0)}
        run_row = next((r for r in rows if r.workflow_id == f"bt:{run.run_id}"), None)
        return {"run_id": run.run_id, "workflow_status": run_row.status if run_row else None,
                "summary": self.summary(run) if run_row else None, "tasks": tasks}

    # --------------------------------------------------------------------------------------------- commands
    def answer(self, run: RunRef, task_id: str, answer: OwnerAnswer) -> str:
        workflow = self._open_task_workflow(run, task_id)
        self.client.send(workflow, answer.model_dump(mode="json"), f"owner:{task_id}",
                         idempotency_key=f"answer:{answer.request_id}")
        return workflow

    def command(self, run: RunRef, kind: str, *, task_id: str | None = None, note: str = "",
                request_id: str | None = None) -> RunCommand:
        command = RunCommand(kind=kind, task_id=task_id, note=note, request_id=request_id or uuid.uuid4().hex)
        self.client.send(f"bt:{run.run_id}", command.model_dump(mode="json"), "run",
                         idempotency_key=f"command:{command.request_id}")
        return command

    def cancel(self, run: RunRef) -> list[str]:
        rows = self.client.list_workflows(workflow_id_prefix=f"bt:{run.run_id}", load_input=False, load_output=False)
        live = [r.workflow_id for r in rows if r.status in ("PENDING", "ENQUEUED")]
        if live:
            self.client.cancel_workflows(live, cancel_children=True)
        return live

    def _open_task_workflow(self, run: RunRef, task_id: str) -> str:
        rows = self.client.list_workflows(workflow_id_prefix=f"bt:{run.run_id}:{task_id}:k", load_input=False,
                                          load_output=False, sort_desc=True)
        for row in rows:
            if row.status == "PENDING":
                return row.workflow_id
        raise LookupError(f"{task_id} has no open task workflow in {run.run_id}")

    def workflows(self, prefix: str) -> Iterable:
        return self.client.list_workflows(workflow_id_prefix=prefix, load_input=False, load_output=False)
