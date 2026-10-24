"""Isolated public API for immutable subplan versions and Git composition candidates."""
from .contracts import Action, Candidate, EvidenceKey, GitPort, GitResult, PropagationChange, SubplanVersion
from .engine import CompositionEngine, propagate, reusable
from .store import Store

__all__ = [
    "Action", "Candidate", "CompositionEngine", "EvidenceKey", "GitPort", "GitResult",
    "PropagationChange", "Store", "SubplanVersion", "propagate", "reusable",
]
