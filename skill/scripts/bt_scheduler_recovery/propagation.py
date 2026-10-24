"""Validated, advice-only selective propagation facts supplied by the composition adapter."""
from __future__ import annotations

from dataclasses import dataclass

from .validation import digest, enum, identifier, reference, require, snapshot

PROPAGATION_ACTIONS = ("none", "reverify", "reintegrate", "audit", "adapt_contract", "modify", "reimplement")


@dataclass(frozen=True)
class DemonstratedFrontier:
    change_id: str
    source_task_id: str
    composition_id: str
    manifest_sha256: str
    tree_digest: str
    action: str
    frontier: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.change_id, self.source_task_id, self.composition_id):
            identifier(value)
        digest(self.manifest_sha256)
        snapshot(self.tree_digest)
        enum(self.action, PROPAGATION_ACTIONS)
        require(type(self.frontier) is tuple and len(self.frontier) <= 128)
        for task_id in self.frontier:
            identifier(task_id)
        require(len(set(self.frontier)) == len(self.frontier))
        require(type(self.evidence_refs) is tuple and 1 <= len(self.evidence_refs) <= 32)
        for evidence_ref in self.evidence_refs:
            reference(evidence_ref)
        require((self.action == "none") == (len(self.frontier) == 0))

    @classmethod
    def from_dict(cls, value: object) -> DemonstratedFrontier:
        require(type(value) is dict)
        expected = {"schema_version", "change_id", "source_task_id", "composition_id", "manifest_sha256",
                    "tree_digest", "action", "frontier", "evidence_refs"}
        require(set(value) == expected, "UNKNOWN_FIELD")
        require(value["schema_version"] == "m5.demonstrated-frontier/1", "SCHEMA_MISMATCH")
        require(type(value["frontier"]) is list and type(value["evidence_refs"]) is list)
        try:
            return cls(value["change_id"], value["source_task_id"], value["composition_id"],
                       value["manifest_sha256"], value["tree_digest"], value["action"],
                       tuple(value["frontier"]), tuple(value["evidence_refs"]))
        except TypeError:
            require(False)

    def to_dict(self) -> dict:
        return {"schema_version": "m5.demonstrated-frontier/1", "change_id": self.change_id,
                "source_task_id": self.source_task_id, "composition_id": self.composition_id,
                "manifest_sha256": self.manifest_sha256, "tree_digest": self.tree_digest,
                "action": self.action, "frontier": list(self.frontier), "evidence_refs": list(self.evidence_refs)}
