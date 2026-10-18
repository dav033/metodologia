"""Dependency graph validation helpers."""


def validate_graph(jobs):
    """Return a validated snapshot of ``jobs`` as dependency sets.

    Graph traversal is iterative so long dependency chains do not depend on
    Python's recursion limit.
    """
    graph = {job_id: set(dependencies) for job_id, dependencies in jobs.items()}

    for job_id, dependencies in graph.items():
        for dependency in dependencies:
            if dependency not in graph:
                raise ValueError("unknown dependency: {!r}".format(dependency))

    # Iterative three-color depth-first search. A gray-to-gray edge is a cycle.
    white, gray, black = 0, 1, 2
    colors = {job_id: white for job_id in graph}
    for root in graph:
        if colors[root] != white:
            continue
        colors[root] = gray
        stack = [(root, iter(graph[root]))]
        while stack:
            node, children = stack[-1]
            try:
                child = next(children)
            except StopIteration:
                colors[node] = black
                stack.pop()
                continue
            if colors[child] == gray:
                raise ValueError("dependency cycle detected")
            if colors[child] == white:
                colors[child] = gray
                stack.append((child, iter(graph[child])))

    return graph
