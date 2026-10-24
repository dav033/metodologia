"""Deterministic, revision-bound project knowledge storage."""
from .store import (
    KnowledgeError,
    ingest,
    query,
    stats,
    export,
    benchmark,
)
from .external import (
    claims_dossier,
    claims_stats,
    external_benchmark,
    ingest_claims,
    invalidate_claims,
    query_claims,
)
from .freshness import FRESHNESS_DAYS

__all__ = ["KnowledgeError", "ingest", "query", "stats", "export", "benchmark", "FRESHNESS_DAYS",
           "ingest_claims", "query_claims", "claims_dossier", "invalidate_claims", "claims_stats",
           "external_benchmark"]
