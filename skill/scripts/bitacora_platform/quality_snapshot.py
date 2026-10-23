"""Bind captured M3 handoffs to immutable M6 source snapshots."""
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from pathlib import Path

import bt_scheduler_executor_adapter as executor_adapter
from bt_scheduler_quality.contracts import VerifyRequest
from bt_scheduler_quality.snapshot import SnapshotSource
from bt_scheduler_quality_orders import to_m1_order as _to_m1_order

m3 = executor_adapter.m3
RepositoryResolver = Callable[[object], object]
LOGGER = logging.getLogger("bt_scheduler_quality_adapter")


def _attempt_worktree(attempts_root: Path, attempt_dir: Path) -> Path | None:
    """`<executor>/ws/worktrees/<same name as the attempt directory>`, only when it really sits there."""
    try:
        parent = (attempts_root.parent / "ws" / "worktrees").resolve(strict=True)
        worktree = (parent / attempt_dir.name).resolve(strict=True)
        worktree.relative_to(parent)
    except (OSError, ValueError):
        return None
    return worktree if worktree.is_dir() else None

def _read_snapshot_inputs(
    executor: m3.AgentExecutor,
    repository_for_order: RepositoryResolver,
    order: VerifyRequest,
) -> tuple[object, object]:
    try:
        return executor.describe(order.attempt_id), repository_for_order(
            _to_m1_order(order)
        )
    # M3 integrations can raise provider-specific exceptions; no provenance means review.
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("M6 attempt description unavailable (%s)", type(error).__name__)
        return None, None

def _captured_handoff(
    description: object, attempt_id: str
) -> tuple[str, Mapping[str, object]] | None:
    if (
        not isinstance(description, Mapping)
        or description.get("attempt_id") != attempt_id
    ):
        return None
    handoff, artifacts = description.get("handoff"), description.get("artifacts")
    if (
        not isinstance(handoff, Mapping)
        or handoff.get("status") != "captured"
        or not isinstance(artifacts, Mapping)
    ):
        return None
    directory = artifacts.get("dir")
    if not isinstance(directory, str):
        return None
    return directory, handoff

def _build_snapshot_source(
    attempts_root: Path,
    attempt_id: str,
    directory: str,
    handoff: Mapping[str, object],
    repository: object,
) -> SnapshotSource | None:
    if not isinstance(repository, (str, Path)):
        return None
    attempt_dir = Path(directory)
    try:
        if ".." in attempt_dir.parts:
            return None
        root = attempts_root.resolve(strict=True)
        attempt_real = attempt_dir.resolve(strict=True)
        attempt_real.relative_to(root)
        if attempt_dir.is_symlink() or not attempt_real.is_dir():
            return None
        expected_manifest = attempt_dir / "handoff" / "manifest.json"
        advertised_manifest = handoff.get("manifest")
        if advertised_manifest is not None and (
            not isinstance(advertised_manifest, str)
            or Path(advertised_manifest) != expected_manifest
        ):
            return None
        repo = Path(repository).resolve(strict=True)
        if not repo.is_dir():
            return None
        base_sha, snapshot_sha = handoff.get("base_sha"), handoff.get("snapshot_sha")
        if not isinstance(base_sha, str) or not isinstance(snapshot_sha, str):
            return None
        return SnapshotSource(
            attempt_id,
            repo,
            attempt_real,
            expected_manifest,
            base_sha,
            snapshot_sha,
            _attempt_worktree(root, attempt_real),
        )
    except (OSError, ValueError):
        return None
