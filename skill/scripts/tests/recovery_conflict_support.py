"""Sanitized source lineage helpers for the REQ-027 structural replay."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE = Path(__file__).with_name("fixtures") / "recovery_req027_conflicts.json"


def load_fixture() -> dict[str, Any]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if value.get("schema") != "recovery-req027-conflicts/2":
        raise ValueError("unsupported REQ-027 conflict fixture")
    return value


def require_complete_paths(source: dict[str, Any]) -> list[str]:
    """Refuse a clipped historical context list as M3 path evidence."""
    unknown = source.get("unknown", {})
    paths = source.get("known", {}).get("complete_merge_paths")
    if unknown.get("complete_merge_paths") or not isinstance(paths, list) or not paths:
        raise ValueError("complete historical merge paths unavailable")
    return paths


def ordered_dag(fixture: dict[str, Any] | None = None) -> dict[str, list[str]]:
    data = fixture or load_fixture()
    return {row["id"]: list(row["after"]) for row in data["ordered_dag"]}
