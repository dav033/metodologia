"""Host adapter for the REQ-029 rollout: stage the accepted upgrade as a private runtime, then conditionally activate it.

`prepare_recovery_runtime` archives exactly the accepted integrated snapshot (never the local, possibly dirty tree) with
the M3 safe extractor, stages it under `.state/recovery-runtimes/<source-digest>` and smoke-tests it isolated; nothing is
installed globally. `activate_recovery_runtime` holds and quiesces only one run, backs up its stores, replaces the
verified old watcher with one started from the staged `bitacora.py` (so its owner/executor children load the tested
code) and enables the one-cycle recovery. A journal makes a crashed activation adoptable through the same steps.
`rollback_recovery_runtime` holds the target and disables recovery; it never restores backups or touches counters.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import bt_recovery_cycle as cycles

RUNTIME_SCHEMA = "recovery-runtime/1"
RECEIPT_SCHEMA = "host-recovery-rollout/1"
BINDING_SCHEMA = "recovery-runtime-binding/1"
JOURNAL = "RUN.recovery-rollout.json"
BINDING = "RUN.recovery-runtime.json"
CURRENT_SCHEMAS = (cycles.POLICY["schema_version"], "recovery-cycles/1", RECEIPT_SCHEMA)
_SHA = re.compile(r"[0-9a-f]{40}")
_SMOKE_MODULES = ("bitacora", "bt_scheduler_watch", "bt_scheduler_ops", "bt_recovery_cycle", "bt_recovery_apply")


class RolloutError(ValueError):
    """Staging or activation was refused; `code` says why."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def _digest(value: object) -> str:
    return cycles.digest(value)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def tree_digest(root: Path) -> str:
    """Digest of every regular file (path and content) below `root`; detects any change of a staged runtime."""
    h = hashlib.sha256()
    for path in sorted(p for p in Path(root).rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(root)
        if "__pycache__" in rel.parts:
            continue
        h.update(str(rel).encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


# ---------------------------------------------------------------- staging
def _check_receipts(receipts: dict, snapshot: str) -> None:
    """The snapshot must be the accepted upgrade integrated tree, named by an accepted M6 gate and every audit."""
    if not isinstance(receipts, dict):
        raise RolloutError("missing_receipts")
    upgrade = receipts.get("upgrade") or {}
    if upgrade.get("snapshot") != snapshot or upgrade.get("accepted") is not True:
        raise RolloutError("upgrade_not_accepted")
    m6 = receipts.get("m6") or {}
    if m6.get("accepted") is not True or m6.get("snapshot") != snapshot or not m6.get("receipt"):
        raise RolloutError("m6_not_accepted")
    audits = receipts.get("audits")
    if not isinstance(audits, list) or not audits:
        raise RolloutError("audit_missing")
    for audit in audits:
        if not isinstance(audit, dict) or audit.get("verdict") != "accepted" or audit.get("snapshot") != snapshot:
            raise RolloutError("audit_not_accepted", str(audit.get("id") if isinstance(audit, dict) else ""))


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    from bt_scheduler_quality.snapshot_git import git_environment

    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=repo, env=git_environment(),
                          capture_output=True, text=True, timeout=30, check=False)


def _smoke(stage: Path, python: str = sys.executable) -> dict:
    """Start the staged CLI and import its entry modules in an isolated interpreter against an empty bitácora root."""
    scripts = stage / "skill" / "scripts"
    probe = ("import sys; sys.path.insert(0, sys.argv[1]); import importlib; "
             "bad = [m for m in sys.argv[2:] if not importlib.import_module(m).__file__.startswith(sys.argv[1])]; "
             "sys.exit(7 if bad else 0)")
    with tempfile.TemporaryDirectory(prefix="recovery-smoke-") as root:
        env = {"PATH": "/usr/bin:/bin", "HOME": root, "BITACORA_ROOT": root, "PYTHONDONTWRITEBYTECODE": "1"}
        runs = [[python, "-I", "-c", probe, str(scripts), *_SMOKE_MODULES], [python, "-I", str(scripts / "bitacora.py"), "--help"]]
        for argv in runs:
            done = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=120, check=False)
            if done.returncode != 0:
                raise RolloutError("smoke_failed", (done.stderr or done.stdout)[-300:])
    return {"ok": True, "modules": list(_SMOKE_MODULES)}


def prepare_recovery_runtime(repo: str | Path, snapshot: str, receipts: dict, state_dir: str | Path, *,
                             smoke: Callable[[Path], dict] | None = None, compatibility: dict | None = None,
                             policy=None) -> dict:
    """Stage `snapshot` (a commit of `repo`) under `<state_dir>/recovery-runtimes/<source-digest>`. Idempotent: an
    existing stage is re-verified and reused. Returns the runtime manifest."""
    from bt_scheduler_quality.contracts import QualityError
    from bt_scheduler_quality.policy import QualityPolicy
    from bt_scheduler_quality.snapshot_archive import SnapshotArchive

    repo, state_dir = Path(repo), Path(state_dir)
    if not isinstance(snapshot, str) or not _SHA.fullmatch(snapshot):
        raise RolloutError("bad_snapshot")
    _check_receipts(receipts, snapshot)
    commits = list(receipts.get("correction_commits") or ())
    for commit in commits:
        if not isinstance(commit, str) or not _SHA.fullmatch(commit) or \
                _git(repo, "merge-base", "--is-ancestor", commit, snapshot).returncode != 0:
            raise RolloutError("correction_commit_not_in_snapshot", str(commit))
    tree = _git(repo, "rev-parse", "--verify", f"{snapshot}^{{tree}}")
    if tree.returncode != 0:
        raise RolloutError("snapshot_unavailable")
    older = compatibility is not None
    if older and not compatibility_ok(compatibility):
        raise RolloutError("incompatible_runtime", "older runtime needs current-schema compatibility evidence")
    evidence = {name: _digest(receipts.get(key)) for name, key in (("upgrade", "upgrade"), ("m6", "m6"),
                                                                    ("audit", "audits"))}
    source = _digest({"snapshot": snapshot, "tree": tree.stdout.strip(), "evidence": evidence})
    base = state_dir / "recovery-runtimes"
    final = base / source
    if final.exists():
        manifest = verify_runtime(final)
        return manifest
    base.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=".stage-", dir=base))
    try:
        archive, stage = work / "snapshot.tar", work / "tree"
        stage.mkdir()
        try:
            archive_sha = SnapshotArchive(policy or QualityPolicy()).write_archive(repo, snapshot, archive)
            SnapshotArchive(policy or QualityPolicy()).extract(archive, stage)
        except QualityError as error:
            raise RolloutError("archive_failed", str(error)) from None
        archive.unlink()
        if not (stage / "skill" / "scripts" / "bitacora.py").is_file():
            raise RolloutError("not_a_skill_tree")
        result = (smoke or _smoke)(stage)
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RolloutError("smoke_failed")
        manifest = {"schema_version": RUNTIME_SCHEMA, "source_digest": source, "snapshot": snapshot,
                    "tree": tree.stdout.strip(), "archive_sha256": archive_sha, "tree_sha256": tree_digest(stage),
                    "evidence_hashes": evidence, "receipts": receipts, "correction_commits": commits,
                    "smoke": result, "older": older, "compatibility": compatibility if older else None,
                    "tested": True}
        _write_json(work / "runtime.json", manifest)
        os.rename(work, final)
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        if final.exists() and (final / "runtime.json").is_file():
            return verify_runtime(final)          # a concurrent preparer won the rename
        raise
    return verify_runtime(final)


def verify_runtime(path: str | Path) -> dict:
    """Re-read a staged runtime and prove its files are still the accepted tree; adds the absolute `bitacora` path."""
    path = Path(path)
    manifest = _read_json(path / "runtime.json")
    if manifest.get("schema_version") != RUNTIME_SCHEMA or manifest.get("tested") is not True:
        raise RolloutError("runtime_not_staged")
    if tree_digest(path / "tree") != manifest.get("tree_sha256"):
        raise RolloutError("runtime_tampered")
    if path.name != manifest.get("source_digest"):
        raise RolloutError("runtime_misplaced")
    return {**manifest, "root": str(path.resolve()),
            "bitacora": str((path / "tree" / "skill" / "scripts" / "bitacora.py").resolve())}


def compatibility_ok(evidence: object) -> bool:
    """An older binary is eligible only with explicit evidence that it reads and writes the current schemas."""
    if not isinstance(evidence, dict) or evidence.get("compatible") is not True or not evidence.get("evidence_ref"):
        return False
    return set(CURRENT_SCHEMAS) <= set(evidence.get("schemas") or ())


# ---------------------------------------------------------------- activation
@dataclass
class Host:
    """Everything activation does to the machine, injectable so tests never touch real processes."""
    sources: Callable[[Path], dict]
    adapter: Callable[[Path], object]
    hold: Callable[[Path, str], None]
    stop_watchers: Callable[[], int]
    stop_owner: Callable[[], int]
    watcher_pids: Callable[[], list]
    watching: Callable[[Path], bool]
    spawn_watch: Callable[[str, Path], int]
    store_paths: Callable[[Path], list]
    preserved: Callable[[Path], dict]
    hold_file: Callable[[Path], dict] = field(default=lambda rdir: {})
    release: Callable[[Path], None] = field(default=lambda rdir: None)
    now: Callable[[], float] = time.time
    wait_watch: float = 15.0


def default_host(project: str, req: str, state_dir: Path) -> Host:
    import bt_run_stores
    import bt_scheduler_adapter as sched
    import bt_scheduler_decisions as decisions
    import bt_scheduler_ops as ops
    import bt_scheduler_recovery_adapter as recovery

    def stop_watchers() -> int:
        pids = ops.watcher_pids(project, req)
        for pid in pids:
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + ops.STOP_SECONDS
        while any(ops._alive(p) for p in pids) and time.monotonic() < deadline:
            time.sleep(0.2)
        for pid in pids:
            if ops._alive(pid):
                with contextlib.suppress(OSError):
                    os.kill(pid, signal.SIGKILL)
        return len(pids)

    def spawn_watch(bitacora: str, rdir: Path) -> int:
        log = state_dir / "watch" / f"{project}-{req}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("ab") as out:
            return subprocess.Popen([sys.executable, bitacora, "--project", project, "scheduler-watch", req],
                                    stdin=subprocess.DEVNULL, stdout=out, stderr=out, start_new_session=True,
                                    close_fds=True).pid

    def store_paths(rdir: Path) -> list:
        found = [p for p in bt_run_stores.paths(rdir).values() if p is not None]
        for p in list(found):
            found += [p.with_suffix(".cycles.json"), p.with_name(p.stem + "-evidence")]
        found += [Path(rdir) / n for n in ("PLAN.json", "PLAN.md", sched.REVISIONS, ops.POLICY_FILE, BINDING,
                                           decisions.ANSWERS, decisions.SUPERSEDED, decisions.NOTIFIED)]
        return [p for p in found if p.exists()]

    def preserved(rdir: Path) -> dict:
        out = {}
        try:
            conn = sqlite3.connect(f"{sched.run_db_path(rdir).resolve().as_uri()}?mode=ro", uri=True, timeout=5)
            try:
                doc = json.loads(conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
            finally:
                conn.close()
            keys = ("attempts", "budget_base", "waits", "reworks", "state")
            out["counters"] = _digest({t: {k: v.get(k) for k in keys} for t, v in (doc.get("tasks") or {}).items()
                                       if isinstance(v, dict)})
        except (sqlite3.Error, TypeError, ValueError, OSError):
            out["counters"] = None
        answers = Path(rdir) / decisions.ANSWERS
        out["decisions"] = hashlib.sha256(answers.read_bytes()).hexdigest() if answers.exists() else None
        return out

    def sources(rdir: Path) -> dict:
        """Bind host authorization to the current M1 revision and read-only recovery evidence."""
        import bt_run_stores

        identity = sched.revision_identity(rdir)
        marker = _read_json(bt_run_stores.runtime_marker(sched.run_db_path(rdir)))
        run_identity = marker.get("runtime_id")
        preview = ops.recovery_preview(rdir)
        current = (isinstance(run_identity, str) and bool(run_identity)
                   and all(identity.get(key) is not None for key in
                           ("plan_id", "revision", "source_sha256", "stop_generation"))
                   and preview.get("schema_version") == "recovery-preview/1")
        return {"run_identity": run_identity, "plan_id": identity.get("plan_id"),
                "revision": identity.get("revision"), "plan_sha256": identity.get("source_sha256"),
                "identity_current": current,
                "stop": {"stopped": bool(identity.get("paused") or identity.get("cancelled")),
                         "generation": identity.get("stop_generation")},
                "recovery_preview": preview}

    def adapter_for(rdir: Path):
        import bt_run_stores

        marker = _read_json(bt_run_stores.runtime_marker(sched.run_db_path(rdir)))
        run_identity = marker.get("runtime_id")
        if not isinstance(run_identity, str) or not run_identity:
            return None
        return recovery.RecoveryAdapter(
            bt_run_stores.module_stores(sched.run_db_path(rdir), run_identity)["m5"],
            scheduler=None, run_id=run_identity, describe=lambda _attempt: None, rdir=rdir,
            recovery_sources=lambda: ops.recovery_preview(rdir)["sources"])

    def hold(rdir: Path, why: str) -> None:
        with ops.hold(rdir, why, keep=True):
            pass

    return Host(sources=sources, adapter=adapter_for, hold=hold, stop_watchers=stop_watchers,
                stop_owner=lambda: ops.stop_owner(project, req), watcher_pids=lambda: ops.watcher_pids(project, req),
                watching=ops.watching, spawn_watch=spawn_watch, store_paths=store_paths, preserved=preserved,
                hold_file=lambda rdir: ops._json_file(ops.hold_path(rdir)),
                release=lambda rdir: ops.hold_path(rdir).unlink(missing_ok=True))


def _backup(host: Host, rdir: Path, dest: Path) -> list:
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for src in host.store_paths(rdir):
        src = Path(src)
        target = dest / src.name
        if src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
        elif src.suffix in (".sqlite3", ".db"):
            source, copy = sqlite3.connect(f"{src.resolve().as_uri()}?mode=ro", uri=True), sqlite3.connect(target)
            try:
                source.backup(copy)
            finally:
                copy.close()
                source.close()
        else:
            shutil.copy2(src, target)
        saved.append(src.name)
    return sorted(saved)


def _check_authorization(auth: dict, runtime: dict, live: dict, adopting: bool, journal: dict) -> None:
    if not isinstance(auth, dict) or auth.get("approved") is not True or not auth.get("ref"):
        raise RolloutError("missing_authorization")
    if runtime.get("older") and not compatibility_ok(runtime.get("compatibility")):
        raise RolloutError("incompatible_runtime")
    if auth.get("runtime_digest") != runtime["source_digest"] or auth.get("evidence_hashes") != runtime["evidence_hashes"]:
        raise RolloutError("evidence_mismatch")
    for key in ("run_identity", "plan_id", "revision", "plan_sha256"):
        if auth.get(key) != live.get(key):
            raise RolloutError("stale_target", key)
    if not live.get("identity_current"):
        raise RolloutError("stale_target", "identity")
    stop = live.get("stop") or {}
    want = journal.get("stop_generation") if adopting else auth.get("stop_generation")
    if adopting:
        return                                          # our own hold is the only stop; hold_at is checked separately
    if stop.get("stopped") or stop.get("generation") != want:
        raise RolloutError("stop_active" if stop.get("stopped") else "stale_stop_generation")


def _receipts(runtime: dict, live: dict, auth: dict, extra: dict) -> list:
    rec = runtime["receipts"]
    base = {"schema_version": RECEIPT_SCHEMA, "authorization_ref": auth["ref"], "runtime_digest": runtime["source_digest"]}
    return [{**base, "source": "M1", "run_identity": live.get("run_identity"), "plan_id": live.get("plan_id"),
             "revision": live.get("revision"), "plan_sha256": live.get("plan_sha256"),
             "stop_generation": auth.get("stop_generation")},
            {**base, "source": "M3", "snapshot": runtime["snapshot"], "tree": runtime["tree"],
             "archive_sha256": runtime["archive_sha256"], "correction_commits": runtime["correction_commits"]},
            {**base, "source": "M6", "receipt": (rec.get("m6") or {}).get("receipt"),
             "snapshot": (rec.get("m6") or {}).get("snapshot"),
             "audit_snapshots": [{"id": a.get("id"), "snapshot": a.get("snapshot")} for a in rec.get("audits", ())]},
            {**base, "source": "host", **extra}]


def activate_recovery_runtime(project: str, req: str, rdir: str | Path, runtime: dict | str | Path,
                              authorization: dict, state_dir: str | Path, *, host: Host | None = None) -> dict:
    """Move one run onto the staged runtime and enable its one-cycle recovery. Safe to call again after a crash: the same
    authorization and runtime adopt the journal and repeat only unfinished steps."""
    rdir, state_dir = Path(rdir), Path(state_dir)
    runtime = verify_runtime(runtime) if not isinstance(runtime, dict) else verify_runtime(runtime["root"])
    host = host or default_host(project, req, state_dir)
    journal_path = rdir / JOURNAL
    journal = _read_json(journal_path)
    ref = (authorization or {}).get("ref")
    adopting = False
    if journal:
        if journal.get("state") == "rolled_back":
            raise RolloutError("rolled_back", "recovery was disabled by rollback")
        if journal.get("authorization_ref") != ref or journal.get("runtime_digest") != runtime["source_digest"]:
            raise RolloutError("authorization_consumed", "this run already has a different activation")
        if journal.get("state") == "active":
            return journal
        adopting = True
    live = host.sources(rdir)
    _check_authorization(authorization, runtime, live, adopting, journal)
    adapter = host.adapter(rdir)
    if adapter is None:
        raise RolloutError("no_runtime_bound")
    try:
        preview = adapter.preview_recovery()
        if not adopting and preview.get("preview_digest") != authorization.get("preview_digest"):
            raise RolloutError("stale_preview")
        watchers = host.watcher_pids()
        if host.watching(rdir) and not watchers and not adopting:
            raise RolloutError("unverified_watch_lock", "a lock is held but no watcher process matches this run")
        if not journal:
            journal = {"schema_version": RECEIPT_SCHEMA, "state": "activating", "authorization_ref": ref,
                       "runtime_digest": runtime["source_digest"], "stop_generation": authorization.get("stop_generation"),
                       "phases": {}, "receipts": []}
        phases = journal["phases"]

        def mark(name: str, **extra) -> None:
            phases[name] = {"at": host.now(), **extra}
            _write_json(journal_path, journal)

        if "held" not in phases:
            host.hold(rdir, f"recovery rollout {ref}")
            mark("held", hold_at=host.hold_file(rdir).get("at"))
        elif "released" not in phases and host.hold_file(rdir).get("at") != phases["held"].get("hold_at"):
            raise RolloutError("stop_won", "the hold changed during activation; nothing further was done")
        elif "released" in phases and (live.get("stop") or {}).get("stopped"):
            raise RolloutError("stop_won", "the owner stopped the run after the hold was released")
        if "quiesced" not in phases:
            mark("quiesced", watchers=host.stop_watchers(), owners=host.stop_owner())
        if "backup" not in phases:
            dest = state_dir / "recovery-backups" / _digest([ref, runtime["source_digest"]])[:16]
            before = host.preserved(rdir)
            mark("backup", path=str(dest), files=_backup(host, rdir, dest), preserved=before)
        if "bound" not in phases:
            previous = _read_json(rdir / BINDING) or None
            _write_json(rdir / BINDING, {"schema_version": BINDING_SCHEMA, "runtime_digest": runtime["source_digest"],
                                         "snapshot": runtime["snapshot"], "bitacora": runtime["bitacora"],
                                         "authorization_ref": ref, "previous": previous})
            mark("bound")
        if "released" not in phases:
            if host.hold_file(rdir).get("at") != phases["held"].get("hold_at"):
                raise RolloutError("stop_won", "the hold changed during activation; nothing further was done")
            host.release(rdir)
            mark("released")
        if "enabled" not in phases:
            policy = _read_json(rdir / "RUN.recovery-policy.json")
            if policy:
                if (policy.get("run_id") != live["run_identity"]
                        or policy.get("authorization_ref") != ref
                        or policy.get("preview_digest") != authorization["preview_digest"]):
                    raise RolloutError("authorization_consumed", "a different recovery policy is already bound")
            else:
                result = adapter.enable_diagnostic_recovery(live["run_identity"], authorization["preview_digest"],
                                                            authorization["stop_generation"], ref)
                if result.get("enabled") is not True:
                    raise RolloutError("activation_refused", str(result.get("blocker", "policy_not_enabled")))
            mark("enabled")
        if "started" not in phases:
            mark("started", pid=host.spawn_watch(runtime["bitacora"], rdir))
            deadline = time.monotonic() + host.wait_watch
            while not host.watching(rdir):
                if time.monotonic() > deadline:
                    raise RolloutError("watcher_not_started")
                time.sleep(0.1)
        after = host.preserved(rdir)
        if after != phases["backup"]["preserved"] and any(after.get(k) != phases["backup"]["preserved"].get(k)
                                                          for k in ("counters", "decisions")):
            journal["preserved_drift"] = {"before": phases["backup"]["preserved"], "after": after}
        journal.update(state="active", receipts=_receipts(runtime, live, authorization, {
            "backup": phases["backup"]["path"], "bitacora": runtime["bitacora"], "preserved": after,
            "adopted": adopting}))
        _write_json(journal_path, journal)
        return journal
    finally:
        with contextlib.suppress(Exception):
            adapter.close()


def rollback_recovery_runtime(project: str, req: str, rdir: str | Path, reason: str, state_dir: str | Path, *,
                              host: Host | None = None) -> dict:
    """Safe rollback: hold the target and disable further recovery. The accepted runtime, evidence, current outcomes
    and counters stay as they are; backups are not restored."""
    rdir = Path(rdir)
    host = host or default_host(project, req, Path(state_dir))
    journal = _read_json(rdir / JOURNAL)
    host.hold(rdir, f"recovery rollback: {reason}")
    host.stop_watchers()
    host.stop_owner()
    policy = _read_json(rdir / "RUN.recovery-policy.json")
    receipts = journal.get("receipts", []) if isinstance(journal, dict) else []
    m1_receipt = next((receipt for receipt in receipts
                       if isinstance(receipt, dict) and receipt.get("source") == "M1"), {})
    _write_json(rdir / "RUN.recovery-policy.json", {
        "schema_version": "recovery-policy-disabled/1", "reason": reason,
        "at": host.now(), "run_identity": policy.get("run_id") or m1_receipt.get("run_identity")})
    journal = {**(journal or {"schema_version": RECEIPT_SCHEMA, "phases": {}, "receipts": []}), "state": "rolled_back",
               "rollback": {"reason": reason, "at": host.now(), "counters_reset": False, "backup_restored": False}}
    _write_json(rdir / JOURNAL, journal)
    return journal
