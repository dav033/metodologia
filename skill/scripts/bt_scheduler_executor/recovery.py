"""Recovery: put every unfinished attempt back under supervision after a restart, never starting a second process."""
from __future__ import annotations

import signal
import time
from typing import Any

from . import artifacts, procinfo
from . import model as m


class RecoverMixin:
    # ================================================================================================ recovery
    def _recover(self) -> None:
        """Before accepting anything: put every unfinished attempt back under supervision, never start a second one."""
        for row in self.ledger.in_states((m.RUNNING,)):       # R10: look at every running attempt now, not at the first tick
            try:
                self._watch(row, act=False)
            except Exception as error:
                self._log(f"recovery watch of {row['attempt_id']} failed: {type(error).__name__}")
        for row in self.ledger.in_states((m.PREPARING, m.SETTLING)):
            if row["state"] == m.SETTLING:
                self._submit_settle(row["attempt_id"], None)
            else:
                self._reconcile_preparing(row)

    def _reconcile_preparing(self, row: dict[str, Any]) -> None:
        """A PREPARING attempt nobody is driving: adopt what is running for it, or prepare it again (idempotent)."""
        adir = self.attempts_dir / row["dirname"]
        info = artifacts.read_shim(adir / "shim.json")
        exited = artifacts.read_exit(adir / "exit.json")
        alive = bool(info and procinfo.alive(info.get("pid"), info.get("ident")))
        if not (info or exited):
            found = procinfo.find_by_argv(str(self.shim_path), str(adir))
            if found:                             # a shim that had not written its record when we died: wait for it
                self._abort_spawn(adir)           # ...and tell it not to start an agent in the meantime
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline and not (info := artifacts.read_shim(adir / "shim.json")):
                    time.sleep(0.05)
                alive = bool(info and procinfo.alive(info.get("pid"), info.get("ident")))
                if not info:                      # it never identified itself, so it never started an agent: stop it
                    for pid in found:
                        procinfo.signal_pid(pid, signal.SIGKILL)
        child_alive = bool(info and procinfo.alive(info.get("child_pid"), info.get("child_ident")))
        if info and (alive or exited or child_alive):     # a dead shim with a live agent: the watcher stops the orphan
            self._adopt_running(row, info)
        elif exited and not info:
            self._submit_settle(row["attempt_id"], exited)
        else:
            with self._guard:
                if row["attempt_id"] in self._starting or row["attempt_id"] in self._settle_busy:
                    return
                self._starting.add(row["attempt_id"])  # nothing is running for it: safe to prepare again
            ws = row.get("workspace")
            if ws and self._workspace_exclusive(row):  # an agent the dead shim started but never recorded still holds the tree
                procinfo.kill_in_cwd(ws["path"], roots=self._sweep_roots(self.attempts_dir / row["dirname"]),
                                     spare_interactive=self.cfg.spare_interactive)
            self._prep_pool.submit(self._launch_job, row["attempt_id"])

    def _adopt_running(self, row: dict[str, Any], info: dict[str, Any]) -> None:
        request = row["request"]
        route = row["route"]
        ws = row.get("workspace") or {}
        event = self._event(row, m.EV_STARTED, "started", {
            "provider": route["provider"], "model": route["model"], "profile": route["profile"],
            "effort": route["effort"], "route": route["reference"], "worktree": ws.get("path"),
            "branch": ws.get("branch"), "base_sha": ws.get("base_sha"), "shim_pid": info.get("pid"),
            "artifacts": artifacts.paths(self.attempts_dir / row["dirname"]), "adopted": True})
        self.ledger.transition(request["attempt_id"], m.RUNNING, expect=(m.PREPARING,), event=event,
                               shim={"pid": info["pid"], "ident": info["ident"], "pgid": info.get("pgid", info["pid"])},
                               started_at=info.get("started_at"))

