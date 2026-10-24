"""Deterministic, revision-bound project knowledge storage."""
from .store import (
    KnowledgeError,
    ingest,
    query,
    stats,
    export,
    benchmark,
)

__all__ = ["KnowledgeError", "ingest", "query", "stats", "export", "benchmark"]
