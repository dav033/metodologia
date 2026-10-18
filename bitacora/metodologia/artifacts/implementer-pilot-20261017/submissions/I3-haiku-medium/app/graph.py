"""Dependency graph snapshotting and validation.

Graphs are plain dicts mapping each job ID to a set of dependency IDs. All
traversals are iterative so long chains do not hit the recursion limit.
"""
from collections import deque


def validate_graph(jobs):
    """Return a fresh ``{job_id: set(dep_ids)}`` snapshot of ``jobs``.

    Dependencies may be any iterable (including generators); they are consumed
    exactly once here. Raises ``ValueError`` for unknown dependencies and for
    cycles, including self-loops and cycles disconnected from other jobs.
    """
    graph = {job_id: set(deps) for job_id, deps in jobs.items()}
    for job_id, deps in graph.items():
        unknown = deps.difference(graph)
        if unknown:
            raise ValueError(
                f"job {job_id!r} depends on unknown job(s): {sorted(unknown)!r}"
            )
    if _has_cycle(graph):
        raise ValueError("dependency graph contains a cycle")
    return graph


def dependents_of(graph):
    """Return ``{job_id: set(ids of jobs that directly depend on job_id)}``.

    ``graph`` must already be validated, so every dependency is a known key.
    """
    dependents = {job_id: set() for job_id in graph}
    for job_id, deps in graph.items():
        for dep in deps:
            dependents[dep].add(job_id)
    return dependents


def _has_cycle(graph):
    """Kahn's algorithm: a cycle exists iff some job is never dequeued."""
    waiting_on = {job_id: len(deps) for job_id, deps in graph.items()}
    dependents = dependents_of(graph)
    queue = deque(job_id for job_id, count in waiting_on.items() if count == 0)
    visited = 0
    while queue:
        job_id = queue.popleft()
        visited += 1
        for child in dependents[job_id]:
            waiting_on[child] -= 1
            if waiting_on[child] == 0:
                queue.append(child)
    return visited != len(graph)
