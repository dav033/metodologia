"""Snapshot and validate dependency graphs without recursive traversal."""

from collections import deque


def validate_graph(jobs):
    """Return fresh dependency sets, rejecting unknown IDs and cycles."""
    graph = {job: set(deps) for job, deps in jobs.items()}
    dependents = {job: [] for job in graph}
    remaining = {job: len(deps) for job, deps in graph.items()}
    for job, deps in graph.items():
        for dependency in deps:
            if dependency not in graph:
                raise ValueError(f"Unknown dependency {dependency!r} for {job!r}")
            dependents[dependency].append(job)

    ready = deque(job for job, count in remaining.items() if count == 0)
    visited = 0
    while ready:
        job = ready.popleft()
        visited += 1
        for dependent in dependents[job]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                ready.append(dependent)
    if visited != len(graph):
        raise ValueError("Dependency graph contains a cycle")
    return graph
