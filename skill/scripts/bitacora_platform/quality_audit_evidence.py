"""Read evidence provenance from the same immutable snapshot the audit gate judges."""
from __future__ import annotations

import json
import re
import shlex
import threading
from contextlib import contextmanager

import bt_audit_gate as audit
from bt_audit_evidence import evidence_paths, safe_path


def check(port, order, raw: bytes | str, gate: audit.Gate) -> audit.Gate:
    data = json.loads(raw)
    task = port.core.plan.task(order.task_id)
    declared = {"verification": task.verification}
    try:
        paths = evidence_paths(data, declared)
    except ValueError as error:
        return audit.Gate(False, (*gate.problems, str(error)), gate.blocking, gate.rework)
    if not paths and "tree_digest" not in data:
        return gate
    tasks = [{"id": t.id, "kind": t.meta.get("kind"), "repository": t.repository,
              "expected_paths": t.expected_paths, "verification": t.verification} for t in port.core.plan.tasks]
    source = port._snapshot_source(order)
    if source is None:
        raise RuntimeError("the audited snapshot is unavailable")
    outputs = audit.evidence_outputs(tasks, task.repository, paths)
    digest_at = lambda revision: audit.tree_digest(source.repository, revision, outputs)
    result = audit.evidence_gate(data, tasks, order.task_id, digest_at(source.snapshot_sha),
                                 lambda path: port._ledger_from_snapshot(order, path), digest_at=digest_at)
    return audit.Gate(gate.ok and result.ok, (*gate.problems, *result.problems), (*gate.blocking, *result.blocking),
                      tuple(dict.fromkeys((*gate.rework, *result.rework))))


def owns_check(port, order, spec) -> bool:
    """A fresh provenance contract replaces legacy private validators, while unrelated checks still execute."""
    task = port.core.plan.task(order.task_id)
    path = audit.ledger_path(task.expected_paths) if task.meta.get("kind") == "audit" else None
    if path is None or not ledger_invocation(spec.command, path):
        return False
    raw = port._read_ledger(order, path)
    gate = audit.evaluate(raw, [t.id for t in port.core.plan.tasks], task.id, port.audit_policy)
    if not gate.ok or raw is None:
        return False
    data = json.loads(raw)
    if not evidence_paths(data, {"verification": task.verification}):
        return False
    result = check(port, order, raw, gate)
    return result.ok and (not port.audit_policy.read_only or not audit.stray_changes(port._read_changes(order), task.expected_paths))


def ledger_invocation(command: str, ledger: str) -> bool:
    """Only recognizable legacy contract checks are replaceable; a ledger argument alone proves no ownership."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        words = list(lexer)
    except ValueError:
        return False
    scripts = [i for i, word in enumerate(words)
               if re.fullmatch(r"(?:check|validate)[-_]findings\.(?:py|[cm]?[jt]sx?|sh)", word.rsplit("/", 1)[-1])]
    if len(scripts) != 1:
        return False
    index = scripts[0]
    if tuple(words[:index]) not in ((), ("npx", "tsx"), ("npx", "--no-install", "tsx"), ("tsx",),
                                   ("node",), ("python",), ("python3",), ("bash",), ("sh",)):
        return False
    tail = words[index + 1:]
    found = False
    while tail:
        word, *tail = tail
        if word == ledger:
            found = True
        elif word == "--check-audit-diff":
            continue
        elif word in ("--ledger", "--integration-results") and tail:
            value, *tail = tail
            if word == "--ledger":
                if value != ledger:
                    return False
                found = True
            elif not safe_path(value):
                return False
        elif word.startswith("--integration-results=") and safe_path(word.split("=", 1)[1]):
            continue
        else:
            return False
    return found


class EvidenceRunner:
    """Bind verification context per worker; one shared runner serves concurrent audit requests."""

    def __init__(self, runner, owns, passed):
        self.runner, self.owns, self.passed = runner, owns, passed
        self.context = threading.local()

    @contextmanager
    def bind(self, order):
        self.context.order = order
        try:
            yield
        finally:
            del self.context.order

    def run(self, spec, snapshot_root, **kwargs):
        order = getattr(self.context, "order", None)
        if order is not None and self.owns(order, spec):
            return self.passed()
        return self.runner.run(spec, snapshot_root, **kwargs)
