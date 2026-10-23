"""Settling: persist the outcome, preserve the work, then close the attempt with exactly one terminal event."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from . import artifacts, classify, handoff, procinfo
from . import model as m
from .errors import ExecutorError
from .model import Route, Workspace

_KIND = {m.FINISHED: m.EV_FINISHED, m.FAILED: m.EV_FAILED, m.CANCELLED: m.EV_CANCELLED}
_SUFFIX = {m.FINISHED: "finished", m.FAILED: "failed", m.CANCELLED: "cancelled"}


class SettleMixin:
    # ================================================================================================ settling
    def _submit_settle(self, attempt_id: str, exit_info: dict[str, Any] | None) -> None:
        with self._guard:
            if attempt_id in self._settling:
                return
            self._settling.add(attempt_id)
        self._settle_pool.submit(self._settle_job, attempt_id, exit_info)

    def _settle_job(self, attempt_id: str, exit_info: dict[str, Any] | None) -> None:
        try:
            self._settle(attempt_id, exit_info)
        except Exception as error:
            self._log(f"settle crashed for {attempt_id}: {type(error).__name__}: {error}")
        finally:
            with self._guard:
                self._settling.discard(attempt_id)
            self._wake.set()

    def _outcome_for(self, row: dict[str, Any], exit_info: dict[str, Any]) -> dict[str, Any]:
        adir = self.attempts_dir / row["dirname"]
        route = Route.from_dict(row["route"])
        raw, total, dropped = ("", 0, 0)
        if exit_info.get("reason") in ("exited", "timeout"):
            raw, total, dropped = artifacts.read_output(adir, exit_info, self.cfg)
        out = classify.outcome(self.driver, route, raw, exit_info, cancel_requested=row["cancel_requested"],
                               state_before=row["state"], totals=(total, dropped))
        out["exit"] = {k: exit_info.get(k) for k in ("started_at", "ended_at", "child_pid") if k in exit_info}
        claim = artifacts.read_claim(adir / "report.json")
        if claim:
            out["claim"] = claim
        return out

    def _settle(self, attempt_id: str, exit_info: dict[str, Any] | None) -> None:
        """Close one attempt. Never runs twice at once for the same attempt (a retry and a first try must not race on
        the handoff files or both stop the orphan)."""
        with self._guard:
            if attempt_id in self._settle_busy:
                return
            self._settle_busy.add(attempt_id)
        try:
            self._settle_once(attempt_id, exit_info)
        finally:
            with self._guard:
                self._settle_busy.discard(attempt_id)

    def _settle_once(self, attempt_id: str, exit_info: dict[str, Any] | None) -> None:
        row = self.ledger.get(attempt_id)
        if row is None or row["state"] in m.TERMINAL:
            return
        adir = self.attempts_dir / row["dirname"]
        first = row["state"] != m.SETTLING
        if first:
            exit_info = exit_info or {"reason": "lost"}
            # whatever the record says, an agent still alive must not keep writing into the tree being preserved: a vanished
            # shim may have left it, and a well-formed exit.json is something the agent itself could have written
            self._stop_orphan(adir)
            try:
                outcome = self._outcome_for(row, exit_info)
            except Exception as error:  # noqa: BLE001 - whatever the files said, the attempt must reach a terminal state
                self._log(f"outcome of {attempt_id} unreadable: {type(error).__name__}")
                outcome = self._outcome_for(row, {"reason": "lost", "error": "outcome could not be computed"})
            if not self.ledger.transition(attempt_id, m.SETTLING, expect=(row["state"],), outcome=outcome):
                return
            row = self.ledger.get(attempt_id) or row
        outcome = row["outcome"]
        # nothing of the agent may outlive it and keep writing. Only on the first pass: a settle retried after a git or disk
        # hiccup must not keep killing whatever (an operator's shell, an editor) has since been opened in the worktree
        if first and row.get("workspace") and self._workspace_exclusive(row):
            self._sweep(row, adir)
        preserved = self._preserve(row, outcome, adir)
        if preserved.get("status") == "failed" and outcome["final"] == m.FINISHED:
            # never a silent success: the agent stopped, but its work could not be preserved. The files are still in the worktree.
            outcome = {**outcome, "final": m.FAILED, "cause": m.ARTIFACT,
                       "detail": f"handoff failed: {preserved.get('error')} {preserved.get('detail', '')}"[:300]}
            self.ledger.update(attempt_id, expect=(m.SETTLING,), outcome=outcome)
        final = outcome["final"]
        event = self._event(row, _KIND[final], _SUFFIX[final], self._terminal_payload(row, outcome, preserved, adir))
        self.ledger.transition(attempt_id, final, expect=(m.SETTLING,), event=event, handoff=preserved,
                               ended_at=self.clock())
        self._heartbeat.pop(attempt_id, None)
        self._cancel_sent.pop(attempt_id, None)
        self._settle_tried.pop(attempt_id, None)

    def _sweep(self, row: dict[str, Any], adir: Path) -> None:
        """Stop agent worktree stragglers while preserving unrelated operator terminals when configured."""
        procinfo.kill_in_cwd(row["workspace"]["path"], roots=self._sweep_roots(adir),
                             spare_interactive=self.cfg.spare_interactive,
                             known_descendants=artifacts.read_descendants(adir / "descendants.json"))

    @staticmethod
    def _sweep_roots(adir: Path) -> dict[int, str]:
        """The recorded shim/agent processes that are still THE SAME processes: a recycled pid is never a root."""
        info = artifacts.read_shim(adir / "shim.json")
        return {pid: ident for pid, ident in ((info.get("pid"), info.get("ident")),
                                             (info.get("child_pid"), info.get("child_ident")))
                if pid and ident and procinfo.alive(pid, ident)}

    def _workspace_exclusive(self, row: dict[str, Any]) -> bool:
        """The cwd sweep is only safe when this attempt is the sole user of its worktree path (a shared directory would
        make it kill a neighbour's agent): refuse to sweep otherwise."""
        path = row["workspace"]["path"]
        return not any(other["attempt_id"] != row["attempt_id"] and (other.get("workspace") or {}).get("path") == path
                       for other in self.ledger.in_states(m.LIVE))

    def _stop_orphan(self, adir: Path) -> None:
        info = artifacts.read_shim(adir / "shim.json")
        if self._kill_child(info):
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and procinfo.alive(info.get("child_pid"), info.get("child_ident")):
                time.sleep(0.05)

    def _preserve(self, row: dict[str, Any], outcome: dict[str, Any], adir: Path) -> dict[str, Any]:
        ws = row.get("workspace")
        if not ws:
            manifest = {"status": "none", "reason": "no workspace was allocated"}
            try:
                (adir / "handoff").mkdir(parents=True, exist_ok=True, mode=0o700)
                artifacts.write_json(adir / "handoff" / "manifest.json", manifest)
            except (ExecutorError, OSError):
                pass
        else:
            manifest = self._capture(row, outcome, adir, Workspace.from_dict(ws))
        title = (artifacts.read_json(adir / "brief.json") or {}).get("title", "")
        try:
            handoff.write_brief(adir, attempt_id=row["attempt_id"], task_id=row["request"]["task_id"], title=title,
                                outcome=outcome["final"], cause=outcome["cause"], manifest=manifest,
                                detail=outcome.get("detail", ""))
        except (OSError, ExecutorError):
            pass
        return manifest

    def _capture(self, row: dict[str, Any], outcome: dict[str, Any], adir: Path, workspace: Workspace) -> dict[str, Any]:
        """The handoff, retried a few times: a transient git or disk error (lock, timeout) must not become a permanent
        "failed" record. If it still fails the work is physically in the worktree and the failure is stated, never hidden."""
        end = float((outcome.get("exit") or {}).get("ended_at") or row.get("updated") or self.clock())
        error: Exception | None = None
        for attempt in range(self.cfg.handoff_tries):
            try:
                return handoff.capture(workspace, adir, dirname=row["dirname"], attempt_id=row["attempt_id"], when=end,
                                       patch_max=self.cfg.patch_max_bytes, mode=self.cfg.handoff_mode,
                                       log_tail=artifacts.log_tail(adir, self.cfg.log_tail_bytes),
                                       declared_paths=(artifacts.read_json(adir / "brief.json") or {}).get("expected_paths") or ())
            except (ExecutorError, OSError) as caught:
                error = caught
                if attempt + 1 < self.cfg.handoff_tries:
                    time.sleep(self.cfg.handoff_retry_seconds * (attempt + 1))
        code = error.code if isinstance(error, ExecutorError) else "ARTIFACT_ERROR"
        detail = error.detail if isinstance(error, ExecutorError) else type(error).__name__
        return {"status": "failed", "error": code, "detail": str(detail)[:300], "worktree": workspace.path,
                "branch": workspace.branch, "base_sha": workspace.base_sha}

    def _terminal_payload(self, row: dict[str, Any], outcome: dict[str, Any], preserved: dict[str, Any],
                          adir: Path) -> dict[str, Any]:
        route = row["route"]
        summary = {k: preserved.get(k) for k in ("status", "base_sha", "branch", "head_sha", "snapshot_sha",
                                                  "has_commits", "commit_count", "dirty", "empty", "changed_total",
                                                  "refs", "worktree", "error", "detail", "reason", "handoff_mode",
                                                  "patch_bytes", "patch_sha256") if k in preserved}
        for key, name in (("manifest", "manifest.json"), ("brief", "continue.md")):
            if (adir / "handoff" / name).exists():              # only paths that exist are advertised
                summary[key] = str(adir / "handoff" / name)
        return {"outcome": outcome["final"], "cause": outcome["cause"], "detail": outcome.get("detail", ""),
                "returncode": outcome.get("returncode"), "signal": outcome.get("signal", ""),
                "reset_epoch": outcome.get("reset_epoch"), "provider": route["provider"], "model": route["model"],
                "profile": route["profile"], "effort": route["effort"], "usage": outcome.get("usage"),
                "cost_usd": outcome.get("cost_usd"), "output": outcome.get("output"),
                "claim": outcome.get("claim"), "handoff": summary, "artifacts": artifacts.paths(adir),
                "note": "facts reported by the executor; acceptance belongs to the independent verifier"}

