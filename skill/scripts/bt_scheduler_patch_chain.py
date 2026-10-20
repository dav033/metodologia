"""Explicit caller-owned cumulative patch transfer; never decides task acceptance.

The caller supplies a trusted candidate-origin receipt for a root task, or a receipt
after independent acceptance for prerequisites, and the exact provenance expected for
each order. Candidate origins transfer code only, never acceptance. All cumulative patches share one pinned
commit. Pass this manager explicitly to M3 with predecessor integration disabled.
Receipts and scratch indexes persist for inspection. release deliberately retains
workspaces. No default executor wiring or snapshot behavior is changed.
"""
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from bt_scheduler_executor_adapter import dirname_of, gitutil, m3

ExecutorError, StartRequest, Workspace, GitWorkspaces = m3.ExecutorError, m3.StartRequest, m3.Workspace, m3.GitWorkspaces


@dataclass(frozen=True)
class PatchChainReceipt:
    """Trusted caller receipt binding provenance, manifest bytes and resulting tree.

    A clean HEAD receipt has empty lineage and no manifest. A candidate root may
    name explicitly unaccepted code origins. A successor receipt must retain that
    candidate provenance followed by every accepted prerequisite attempt in order,
    including the producer of its cumulative patch. The caller distinguishes origin
    provenance from accepted prerequisites; lineage alone grants no acceptance.
    manifest_sha256 binds the schema-2 handoff manifest, which binds patch bytes.
    Caller must bind these receipts to its frozen plan; this module cannot accept a task.
    """

    base_sha: str
    target_tree: str
    lineage: tuple[str, ...] = ()
    manifest_path: str | None = None
    manifest_sha256: str | None = None


def _fail(message: str) -> None:
    raise ExecutorError("WORKSPACE_ERROR", message)


def _encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class PatchChainWorkspaces:
    """WorkspaceManager wrapper for a single explicitly serialized accepted chain.

    source(request) returns trusted PatchChainReceipt. expected_lineage(request)
    independently lists candidate origins plus accepted predecessor attempt ids.
    Reallocation succeeds only while workspace content still equals the prepared
    input tree; it never resets agent edits. materialize_empty requires a
    delegate that creates empty no-checkout worktrees; cached patches are verified
    before checkout-index materializes files, allowing already-absent baseline
    paths without deleting any file. Caller must reject new deletions during review. A partial interrupted allocation fails
    closed and needs operator inspection. root must be private to this run.
    """

    def __init__(self, delegate: GitWorkspaces,
                 source: Callable[[StartRequest], PatchChainReceipt],
                 receipts_root: Path | str,
                 expected_lineage: Callable[[StartRequest], tuple[str, ...]],
                 *, materialize_empty: bool = False):
        self.delegate = delegate
        self.source = source
        self.root = Path(receipts_root)
        self.expected_lineage = expected_lineage
        self._lock = threading.Lock()
        self.materialize_empty = materialize_empty

    def _receipt(self, request: StartRequest) -> tuple[PatchChainReceipt, bytes | None]:
        receipt = self.source(request)
        if receipt.lineage != tuple(self.expected_lineage(request)):
            _fail("receipt omits or changes accepted predecessor lineage")
        base = self.delegate.check(request)
        if base != receipt.base_sha or request.base_ref != receipt.base_sha:
            _fail("patch chain requires the exact pinned base SHA")
        if not receipt.lineage:
            if receipt.manifest_path or receipt.manifest_sha256:
                _fail("root receipt cannot contain a predecessor patch")
            tree = gitutil.run(self.delegate.repository(request.repository),
                               ["rev-parse", f"{base}^{{tree}}"])
            if tree != receipt.target_tree:
                _fail("baseline target tree differs from pinned HEAD")
            return receipt, None
        if not receipt.manifest_path or not receipt.manifest_sha256:
            _fail("accepted predecessor requires a bound schema-2 manifest")
        raw = Path(receipt.manifest_path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt.manifest_sha256:
            _fail("handoff manifest digest mismatch")
        manifest = json.loads(raw)
        if (manifest.get("schema") != 2 or manifest.get("handoff_mode") != "patch"
                or manifest.get("status") != "captured" or manifest.get("base_sha") != base
                or manifest.get("head_sha") != base or manifest.get("has_commits")
                or manifest.get("attempt_id") != receipt.lineage[-1]):
            _fail("handoff identity, schema, mode, status or base mismatch")
        patch = manifest.get("patch", {})
        data = Path(patch["path"]).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if (patch.get("bytes") != len(data) or patch.get("sha256") != digest
                or manifest.get("patch_bytes") != len(data)
                or manifest.get("patch_sha256") != digest):
            _fail("handoff patch size or digest mismatch")
        if not self.materialize_empty and b"\ndeleted file mode " in b"\n" + data:
            _fail("patch deletes files; prohibited in this run")
        return receipt, data

    def check(self, request: StartRequest) -> str:
        receipt, _ = self._receipt(request)
        return receipt.base_sha

    def _tree(self, ws: Workspace) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        index = self.root / f"index-{uuid.uuid4().hex}"
        env = {"GIT_INDEX_FILE": str(index)}
        gitutil.run(ws.path, ["read-tree", "HEAD"], env=env)
        gitutil.run(ws.path, ["add", "-A"], env=env)
        return gitutil.run(ws.path, ["write-tree"], env=env)

    def allocate(self, request: StartRequest) -> Workspace:
        with self._lock:
            receipt, patch = self._receipt(request)
            identity = {"receipt": asdict(receipt), "plan_id": request.plan_id,
                        "revision": request.revision, "plan_sha256": request.plan_sha256,
                        "task_id": request.task_id, "attempt_id": request.attempt_id}
            fingerprint = hashlib.sha256(_encoded(identity)).hexdigest()
            self.root.mkdir(parents=True, exist_ok=True)
            record = self.root / f"{dirname_of(request.attempt_id)}.json"
            prior = json.loads(record.read_bytes()) if record.exists() else None
            if prior and (prior.get("fingerprint") != fingerprint or prior.get("state") != "prepared"):
                _fail("changed receipt or interrupted preparation; inspect persisted evidence")
            ws = self.delegate.allocate(request)
            if ws.base_sha != receipt.base_sha or gitutil.run(ws.path, ["rev-parse", "HEAD"]) != receipt.base_sha:
                _fail("workspace HEAD differs from pinned base")
            if prior:
                if self._tree(ws) != receipt.target_tree:
                    _fail("allocated workspace was edited; refusing to overwrite agent changes")
                return ws
            if self.materialize_empty:
                if any(p.name != ".git" for p in Path(ws.path).iterdir()):
                    _fail("materialize_empty requires an empty no-checkout worktree")
            elif gitutil.run(ws.path, ["status", "--porcelain=v1", "--untracked-files=all"]):
                _fail("fresh workspace contains existing changes")
            record.write_bytes(_encoded({**identity, "fingerprint": fingerprint, "state": "preparing"}))
            env = None
            if self.materialize_empty:
                env = {"GIT_INDEX_FILE": str((self.root / f"materialize-{uuid.uuid4().hex}").resolve())}
                gitutil.run(ws.path, ["read-tree", receipt.base_sha], env=env)
            if patch:
                # Apply exactly the already-verified bytes, not a mutable source path.
                frozen = self.root / f"{dirname_of(request.attempt_id)}.input.patch"
                with frozen.open("xb") as handle:
                    handle.write(patch)
                mode = "--cached" if self.materialize_empty else "--index"
                gitutil.run(ws.path, ["apply", "--check", mode, str(frozen.resolve())], env=env)
                gitutil.run(ws.path, ["apply", mode, str(frozen.resolve())], env=env)
            if self.materialize_empty:
                if gitutil.run(ws.path, ["write-tree"], env=env) != receipt.target_tree:
                    _fail("cached cumulative tree differs from trusted receipt")
                gitutil.run(ws.path, ["checkout-index", "--all"], env=env)
                gitutil.run(ws.path, ["read-tree", receipt.target_tree])
            if self._tree(ws) != receipt.target_tree:
                _fail("restored cumulative tree differs from trusted receipt")
            # Compare trees for deletions as well: patch syntax alone is insufficient.
            deleted = gitutil.run(ws.path, ["diff", "--cached", "--diff-filter=D", "--name-only", receipt.base_sha])
            if deleted and not self.materialize_empty:
                _fail("restored tree deletes base paths")
            record.write_bytes(_encoded({**identity, "fingerprint": fingerprint, "state": "prepared",
                                         "workspace": ws.to_dict()}))
            return ws

    def release(self, workspace: Workspace) -> None:
        """Retain all evidence: deletion is prohibited for this isolated run."""
