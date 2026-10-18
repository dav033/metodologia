"""Validation helpers for dependency graphs."""

from collections import deque
from collections.abc import Mapping


def validate_graph(jobs):
    """Return a snapshot of ``jobs`` after validating its dependencies.

    The returned mapping and each dependency set are new objects, so later
    changes to the input do not alter the validated graph.
    """
    if not isinstance(jobs, Mapping):
        raise ValueError("jobs must be a mapping")

    graph = {}
    for job_id, dependencies in jobs.items():
        if not isinstance(job_id, str) or not job_id:
            raise ValueError("job IDs must be nonempty strings")
        try:
            dependency_ids = set(dependencies)
        except TypeError as error:
            raise ValueError("each job's dependencies must be iterable") from error

        if any(not isinstance(dependency, str) or not dependency for dependency in dependency_ids):
            raise ValueError("dependency IDs must be nonempty strings")
        graph[job_id] = dependency_ids

    for job_id, dependencies in graph.items():
        unknown = dependencies.difference(graph)
        if unknown:
            raise ValueError(
                "job {!r} has unknown dependencies: {}".format(
                    job_id, ", ".join(sorted(unknown))
                )
            )

    # Kahn's algorithm checks every component without using Python recursion.
    remaining_dependencies = {
        job_id: len(dependencies) for job_id, dependencies in graph.items()
    }
    dependents = {job_id: [] for job_id in graph}
    for job_id, dependencies in graph.items():
        for dependency in dependencies:
            dependents[dependency].append(job_id)

    ready = deque(
        job_id
        for job_id, count in remaining_dependencies.items()
        if count == 0
    )
    visited_count = 0
    while ready:
        completed = ready.popleft()
        visited_count += 1
        for dependent in dependents[completed]:
            remaining_dependencies[dependent] -= 1
            if remaining_dependencies[dependent] == 0:
                ready.append(dependent)

    if visited_count != len(graph):
        raise ValueError("dependency graph contains a cycle")

    return graph
