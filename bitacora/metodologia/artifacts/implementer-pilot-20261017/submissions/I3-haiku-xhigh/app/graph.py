"""Dependency graph validation and inversion helpers."""
from collections import deque


def validate_graph(jobs):
    """Return a fresh ``{job: set(dependencies)}`` mapping for ``jobs``.

    Each dependency iterable is consumed exactly once, so generators are
    supported and the result does not alias the caller's data. Raises
    ValueError for unknown dependencies and for cycles, including self-loops
    and cycles disconnected from the rest of the graph.
    """
    graph = {job: set(deps) for job, deps in jobs.items()}
    _reject_unknown_dependencies(graph)
    _reject_cycles(graph)
    return graph


def invert_graph(graph):
    """Return ``{job: set(jobs that directly depend on job)}`` for a validated graph."""
    dependents = {job: set() for job in graph}
    for job, deps in graph.items():
        for dep in deps:
            dependents[dep].add(job)
    return dependents


def _reject_unknown_dependencies(graph):
    for job, deps in graph.items():
        unknown = deps.difference(graph)
        if unknown:
            raise ValueError(
                f'job {job!r} depends on unknown job(s) {sorted(unknown)!r}'
            )


def _reject_cycles(graph):
    """Kahn's algorithm: peel off jobs whose dependencies are all resolved.

    Iterative on purpose, so long dependency chains cannot exhaust the
    interpreter's recursion limit. Any job never peeled off is on a cycle or
    downstream of one.
    """
    dependents = invert_graph(graph)
    unmet = {job: len(deps) for job, deps in graph.items()}
    queue = deque(job for job, count in unmet.items() if count == 0)
    resolved = 0
    while queue:
        job = queue.popleft()
        resolved += 1
        for child in dependents[job]:
            unmet[child] -= 1
            if unmet[child] == 0:
                queue.append(child)
    if resolved != len(graph):
        unresolved = sorted(job for job, count in unmet.items() if count > 0)
        raise ValueError(f'dependency cycle detected; unresolved jobs {unresolved!r}')
