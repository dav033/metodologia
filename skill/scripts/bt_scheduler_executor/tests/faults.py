"""Run an executor in THIS process, kill it hard (os._exit) at a named point, so a test can restart it and check what is left.

usage: python faults.py <workdir> <crash point> <scenario>   (the repository and the executor root live under <workdir>)
Exit status 137 means "crashed at the requested point"; anything else means the point was never reached.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]
import bt_scheduler_executor as ex
import support
from bt_scheduler_executor import handoff as handoff_module
from bt_scheduler_executor import model as m

POINTS = ("after_accept", "after_allocate", "before_running_txn", "after_running_txn", "before_settling_txn",
          "after_settling_txn", "during_handoff", "after_handoff", "before_terminal_txn", "after_terminal_txn",
          "after_delivery_before_mark")


class FileSink:
    """Appends every delivery to <workdir>/sink.jsonl, so both the dying and the restarted executor are observable."""

    def __init__(self, path: Path, hook=None):
        self.path, self.hook = Path(path), hook

    def deliver(self, event):
        with open(self.path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(event.to_dict()) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if self.hook:
            self.hook(event)

    def rows(self):
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]


def die(*_, **__):
    os._exit(137)


def build(workdir: Path, hook=None, autostart=True):
    repo = workdir / "repo"
    if not repo.exists():
        support.make_repo(repo)
    config = ex.Config(poll_seconds=0.05, heartbeat_seconds=3600, grace_seconds=1.0, timeout_seconds=60)
    sink = FileSink(workdir / "sink.jsonl", hook)
    workspaces = ex.GitWorkspaces(workdir / "exec-root" / "ws", {"main": repo})
    x = ex.AgentExecutor(workdir / "exec-root", resolver=support.FakeResolver(), briefs=support.FakeBriefs(),
                         driver=support.FakeDriver(), workspaces=workspaces, sink=sink, config=config,
                         autostart=autostart)
    return x, sink


def main() -> None:
    workdir, point, scenario = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    assert point in POINTS, point
    first_mark = {"done": False}
    hook = None
    x, sink = build(workdir, autostart=False)
    if point == "after_delivery_before_mark":
        orig_mark = x.ledger.mark_delivered

        def mark(event_id):
            if event_id.endswith(":finished"):
                die()
            orig_mark(event_id)
        x.ledger.mark_delivered = mark
    if point in ("before_running_txn", "after_running_txn", "before_settling_txn", "after_settling_txn",
                 "before_terminal_txn", "after_terminal_txn"):
        orig = x.ledger.transition
        want = {"before_running_txn": (m.RUNNING, True), "after_running_txn": (m.RUNNING, False),
                "before_settling_txn": (m.SETTLING, True), "after_settling_txn": (m.SETTLING, False),
                "before_terminal_txn": (m.FINISHED, True), "after_terminal_txn": (m.FINISHED, False)}[point]

        def transition(attempt_id, to, **kw):
            if to == want[0] and want[1]:
                die()
            result = orig(attempt_id, to, **kw)
            if to == want[0] and not want[1] and result:
                die()
            return result
        x.ledger.transition = transition
    if point == "after_allocate":
        orig_alloc = x.workspaces.allocate

        def allocate(request):
            ws = orig_alloc(request)
            die()
            return ws
        x.workspaces.allocate = allocate
    if point == "during_handoff":
        handoff_module.capture = die
    if point == "after_handoff":
        orig_capture = handoff_module.capture

        def capture(*a, **kw):
            result = orig_capture(*a, **kw)
            die()
            return result
        handoff_module.capture = capture
    request = support.order(1, scenario)
    receipt = x.start(request)
    if point == "after_accept":
        die()
    x.start_loop()
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        time.sleep(0.05)
    sys.exit(2)                       # the crash point was never reached


if __name__ == "__main__":
    main()
