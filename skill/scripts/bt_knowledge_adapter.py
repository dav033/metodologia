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


def ingest_claims(db_path: str | Path, document: object) -> dict:
    return bt_knowledge.ingest_claims(db_path, document)


def query_claims(db_path: str | Path, project: str, *, topic: str | None = None, kind: str | None = None,
                 facts_only: bool = False) -> list[dict]:
    return bt_knowledge.query_claims(db_path, project, topic=topic, kind=kind, facts_only=facts_only)


def claims_dossier(db_path: str | Path, project: str, subplan: str, *, max_bytes: int = 12000) -> str:
    return bt_knowledge.claims_dossier(db_path, project, subplan, max_bytes=max_bytes)


def invalidate_claims(db_path: str | Path, project: str, topic: str, reason: str, *, kind: str | None = None) -> dict:
    return bt_knowledge.invalidate_claims(db_path, project, topic, reason, kind=kind)


def claims_stats(db_path: str | Path, project: str) -> dict:
    return bt_knowledge.claims_stats(db_path, project)
