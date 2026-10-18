"""Dependency graph validation and adjacency helpers.

All traversals are iterative so that long dependency chains do not hit the
interpreter's recursion limit.
"""
from collections import deque
from collections.abc import Mapping


def validate_graph(jobs):
    """Return a fresh, validated snapshot ``{job_id: set(dependency_ids)}``.

    Dependency iterables (including generators) are consumed exactly once, so
    later changes to the caller's input do not affect the result. Duplicate
    dependencies collapse into one entry.

    Raises:
        TypeError: if ``jobs`` is not a mapping.
        ValueError: if a job depends on an unknown job, or if the graph
            contains a cycle (self-loops and disconnected cycles included).
    """
    if not isinstance(jobs, Mapping):
        raise TypeError('jobs must be a mapping of job IDs to dependency iterables')
    graph = {job: set(deps) for job, deps in jobs.items()}
    _check_known_dependencies(graph)
    _check_acyclic(graph)
    return graph


def dependents_of(graph):
    """Return the reverse adjacency map ``{job_id: set(ids depending on it)}``.

    ``graph`` must already be validated; every dependency must be a key.
    """
    dependents = {job: set() for job in graph}
    for job, deps in graph.items():
        for dep in deps:
            dependents[dep].add(job)
    return dependents


def _check_known_dependencies(graph):
    for job, deps in graph.items():
        for dep in deps:
            if dep not in graph:
                raise ValueError(f'job {job!r} depends on unknown job {dep!r}')


def _check_acyclic(graph):
    """Kahn's algorithm: every job must be reachable once its dependencies are."""
    remaining = {job: len(deps) for job, deps in graph.items()}
    dependents = dependents_of(graph)
    queue = deque(job for job, count in remaining.items() if count == 0)
    processed = 0
    while queue:
        job = queue.popleft()
        processed += 1
        for dependent in dependents[job]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                queue.append(dependent)
    if processed != len(graph):
        cyclic = sorted(job for job, count in remaining.items() if count > 0)
        raise ValueError(f'dependency cycle detected involving {cyclic}')
