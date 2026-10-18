from collections import deque


def validate_graph(jobs):
    """Return a fresh dict job -> set(deps); raise ValueError on unknown deps or cycles."""
    graph = {job: set(deps) for job, deps in jobs.items()}
    for job, deps in graph.items():
        for dep in deps:
            if dep not in graph:
                raise ValueError(f"unknown dependency {dep!r} for job {job!r}")
    # Kahn's algorithm (iterative, so long chains are safe).
    remaining = {job: len(deps) for job, deps in graph.items()}
    dependents = build_dependents(graph)
    queue = deque(job for job, n in remaining.items() if n == 0)
    seen = 0
    while queue:
        job = queue.popleft()
        seen += 1
        for child in dependents[job]:
            remaining[child] -= 1
            if remaining[child] == 0:
                queue.append(child)
    if seen != len(graph):
        raise ValueError("dependency cycle detected")
    return graph


def build_dependents(graph):
    """Map each job to the set of jobs that depend on it."""
    dependents = {job: set() for job in graph}
    for job, deps in graph.items():
        for dep in deps:
            dependents[dep].add(job)
    return dependents
