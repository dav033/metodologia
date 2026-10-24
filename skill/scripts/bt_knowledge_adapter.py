"""The methodology boundary for the standalone knowledge package."""
from __future__ import annotations

from pathlib import Path

import bt_knowledge

KnowledgeError = bt_knowledge.KnowledgeError


def ingest(db_path: str | Path, delta: object, repo_path: str | Path | None = None) -> dict:
    return bt_knowledge.ingest(db_path, delta, repo_path)


def query(db_path: str | Path, project: str, *, commit: str | None = None, area: str | None = None,
          status: str | None = None, repo_path: str | Path | None = None) -> list[dict]:
    return bt_knowledge.query(db_path, project, commit=commit, area=area, status=status, repo_path=repo_path)


def export(db_path: str | Path, project: str, format: str, *, commit: str | None = None) -> str:
    return bt_knowledge.export(db_path, project, format, commit=commit)


def stats(db_path: str | Path, project: str) -> dict:
    return bt_knowledge.stats(db_path, project)
