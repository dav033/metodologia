"""Operator side of the durable runtime: start, observe and steer runs through the DBOS system database.

The engine service executes workflows; this client never does. It enqueues run workflows by name (with their
deterministic ID, so a repeated `start` returns the existing run), sends owner answers and run commands, reads the
`summary`/`state`/`decision` events, and cancels. Every message is validated against the owner contracts first.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterable

from bt_contracts.execution import LegacyProgress, RunRef
from bt_contracts.owner import OwnerAnswer, RunCommand
from dbos import DBOSClient, EnqueueOptions, SetWorkflowID

from .execution.engine import APP_VERSION, RUNS
from .settings import Settings

RUN_WORKFLOW, TASK_WORKFLOW = "bt.run", "bt.task"


def progress_input(legacy: LegacyProgress | None) -> dict:
    """The run workflow's starting progress as sent: fields added after an engine release (`paused`, a task's
    `integrated`, D-149/D-150) travel only when set, so an engine that predates them still takes every input it can run
    as asked (one that cannot honour a pause or a copied line refuses it instead of ignoring it)."""
    data = (legacy or LegacyProgress()).model_dump(mode="json")
    if not data.get("paused"):
        data.pop("paused", None)
    for task in data.get("tasks") or []:
        if not task.get("integrated"):
            task.pop("integrated", None)
    return data


class Client:
    def __init__(self, system_database_url: str):
        self.client = DBOSClient(system_database_url=system_database_url)

    def close(self) -> None:
        self.client.destroy()

    # ----------------------------------------------------------------------------------------------- runs
    def start(self, run: RunRef, settings: Settings, legacy: LegacyProgress | None = None) -> str:
        workflow_id = f"bt:{run.run_id}"
        options: EnqueueOptions = {"workflow_name": RUN_WORKFLOW, "queue_name": RUNS, "workflow_id": workflow_id,
                                   "app_version": APP_VERSION}
        existing = self.client.list_workflows(workflow_ids=[workflow_id], load_input=False, load_output=False)
        if not existing:
            self.client.enqueue(options, run.model_dump(mode="json"), settings.model_dump(mode="json"),
                                progress_input(legacy))
        return workflow_id

    def current_run_workflow(self, run: RunRef) -> str:
        """The run workflow that owns the run now: `bt:<run>`, or after `reopen` its latest incarnation `bt:<run>@N`."""
        base = f"bt:{run.run_id}"
        rows = self.client.list_workflows(workflow_id_prefix=base + "@", load_input=False, load_output=False)
        numbers = [int(r.workflow_id.rsplit("@", 1)[1]) for r in rows if r.workflow_id.rsplit("@", 1)[1].isdigit()]
        return f"{base}@{max(numbers)}" if numbers else base

    def reopen(self, run: RunRef) -> str:
        """Fork the run's ended incarnation at its final summary into the next one (`bt:<run>@N`). The fork replays
        the history up to there and, instead of ending blocked again, waits for the owner's next command
        (`bt-run-reopened`). A run whose workflow has not ended needs no reopening and is returned as it is."""
        current = self.current_run_workflow(run)
        rows = self.client.list_workflows(workflow_ids=[current], load_input=False, load_output=False)
        if not rows:
            raise LookupError(f"{run.run_id} has no run workflow")
        if rows[0].status != "SUCCESS":
            return current
        final = [step["function_id"] for step in self.client.list_workflow_steps(current)
                 if step["function_name"] == "DBOS.setEvent"]
        if not final:
            raise RuntimeError(f"REOPEN_UNSUPPORTED: {current} recorded no summary")
        number = int(current.rsplit("@", 1)[1]) + 1 if "@" in current[len(f"bt:{run.run_id}"):] else 2
        with SetWorkflowID(f"bt:{run.run_id}@{number}"):
            handle = self.client.fork_workflow(current, max(final))
        return handle.workflow_id

    def summary(self, run: RunRef) -> dict | None:
        return self.client.get_event(self.current_run_workflow(run), "summary", timeout_seconds=0)

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
        current = self.current_run_workflow(run)
        run_row = next((r for r in rows if r.workflow_id == current), None)
        return {"run_id": run.run_id, "workflow_id": current, "workflow_status": run_row.status if run_row else None,
                "summary": self.summary(run) if run_row else None, "tasks": tasks}

    # --------------------------------------------------------------------------------------------- commands
    def answer(self, run: RunRef, task_id: str, answer: OwnerAnswer, round_no: int | None = None) -> str:
        """Send `answer` to the task's open round, or to round `round_no` exactly (an answer built for an older
        round must not reach a newer one: request ids restart at d1 in every round). One answer per request id and
        round: DBOS scopes the idempotency key to the destination workflow."""
        workflow = self._open_task_workflow(run, task_id) if round_no is None else \
            self._round_workflow(run, task_id, round_no)
        self.client.send(workflow, answer.model_dump(mode="json"), f"owner:{task_id}",
                         idempotency_key=f"answer:{answer.request_id}")
        return workflow

    def command(self, run: RunRef, kind: str, *, task_id: str | None = None, note: str = "",
                request_id: str | None = None, by: str = "owner", expect_paused: bool | None = None,
                expect_round: int | None = None) -> RunCommand:
        """A run command, applied at most once per request id. `expect_*` name the state the command was built
        against; the run workflow refuses it when the run moved on. Unset fields are not sent, so a command without
        them is the same message older engines accept."""
        command = RunCommand(kind=kind, task_id=task_id, note=note, request_id=request_id or uuid.uuid4().hex, by=by,
                             expect_paused=expect_paused, expect_round=expect_round)
        # a retry of a run that already ended blocked reopens it first: a message to an ended workflow is never read
        target = self.reopen(run) if kind == "retry_task" else self.current_run_workflow(run)
        self.client.send(target, command.model_dump(mode="json", exclude_none=True), "run",
                         idempotency_key=f"command:{command.request_id}")
        return command

    def cancel(self, run: RunRef) -> list[str]:
        rows = self.client.list_workflows(workflow_id_prefix=f"bt:{run.run_id}", load_input=False, load_output=False)
        live = [r.workflow_id for r in rows if r.status in ("PENDING", "ENQUEUED")]
        if live:
            self.client.cancel_workflows(live, cancel_children=True)
        return live

    def _round_workflow(self, run: RunRef, task_id: str, round_no: int) -> str:
        workflow = f"bt:{run.run_id}:{task_id}:k{round_no}"
        rows = self.client.list_workflows(workflow_ids=[workflow], load_input=False, load_output=False)
        if not rows or rows[0].status != "PENDING":
            raise LookupError(f"{task_id} round {round_no} is not open in {run.run_id}")
        return workflow

    def _open_task_workflow(self, run: RunRef, task_id: str) -> str:
        rows = self.client.list_workflows(workflow_id_prefix=f"bt:{run.run_id}:{task_id}:k", load_input=False,
                                          load_output=False, sort_desc=True)
        for row in rows:
            if row.status == "PENDING":
                return row.workflow_id
        raise LookupError(f"{task_id} has no open task workflow in {run.run_id}")

    def workflows(self, prefix: str) -> Iterable:
        return self.client.list_workflows(workflow_id_prefix=prefix, load_input=False, load_output=False)
