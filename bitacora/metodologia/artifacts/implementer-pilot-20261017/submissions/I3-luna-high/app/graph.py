"""Dependency graph validation helpers."""

from collections import deque
from collections.abc import Mapping


def validate_graph(jobs):
    """Return an independent dependency-set snapshot of a valid job graph.

    Every dependency must name a job in ``jobs``. Cycles are detected with an
    iterative topological traversal so validation also works for deep graphs.
    """
    if not isinstance(jobs, Mapping):
        raise ValueError("jobs must be a mapping")

    graph = {}
    for job_id, dependencies in jobs.items():
        if not isinstance(job_id, str) or not job_id:
            raise ValueError("job IDs must be nonempty strings")
        try:
            graph[job_id] = set(dependencies)
        except TypeError as exc:
            raise ValueError("dependencies must be iterable") from exc

    known_jobs = set(graph)
    for job_id, dependencies in graph.items():
        if any(not isinstance(dep, str) or not dep for dep in dependencies):
            raise ValueError("dependency IDs must be nonempty strings")
        unknown = dependencies - known_jobs
        if unknown:
            raise ValueError(
                "unknown dependency for {!r}: {!r}".format(job_id, min(unknown))
            )

    dependents = {job_id: [] for job_id in graph}
    remaining = {}
    for job_id, dependencies in graph.items():
        remaining[job_id] = len(dependencies)
        for dependency in dependencies:
            dependents[dependency].append(job_id)

    ready = deque(job_id for job_id, count in remaining.items() if count == 0)
    visited = 0
    while ready:
        job_id = ready.popleft()
        visited += 1
        for dependent in dependents[job_id]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                ready.append(dependent)

    if visited != len(graph):
        raise ValueError("dependency graph contains a cycle")
    return graph
