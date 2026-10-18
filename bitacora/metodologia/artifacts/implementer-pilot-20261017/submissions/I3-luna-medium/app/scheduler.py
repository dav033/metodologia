"""Single-threaded dependency scheduler."""

from .graph import validate_graph


class Scheduler:
    def __init__(self, jobs, max_parallel=2):
        if isinstance(max_parallel, bool) or not isinstance(max_parallel, int) or max_parallel < 1:
            raise ValueError("max_parallel must be an integer of at least 1")

        self.jobs = validate_graph(jobs)
        self.max_parallel = max_parallel
        self.state = {job_id: "pending" for job_id in self.jobs}
        self._dependents = {job_id: set() for job_id in self.jobs}
        for job_id, dependencies in self.jobs.items():
            for dependency in dependencies:
                self._dependents[dependency].add(job_id)

    def ready(self):
        """Return all pending jobs whose dependencies have succeeded."""
        return sorted(
            job_id
            for job_id, dependencies in self.jobs.items()
            if self.state[job_id] == "pending"
            and all(self.state[dependency] == "succeeded" for dependency in dependencies)
        )

    def start(self, job_id):
        if (
            job_id not in self.state
            or self.state[job_id] != "pending"
            or any(self.state[dependency] != "succeeded" for dependency in self.jobs[job_id])
            or sum(status == "running" for status in self.state.values()) >= self.max_parallel
        ):
            raise ValueError("job cannot be started")
        self.state[job_id] = "running"

    def finish(self, job_id, success=True):
        if job_id not in self.state or self.state[job_id] != "running":
            raise ValueError("job is not running")
        if success:
            self.state[job_id] = "succeeded"
            return

        self.state[job_id] = "failed"
        # Mark pending descendants blocked as soon as this failure is known.
        # Continue traversal through each newly blocked job to reach all descendants.
        stack = list(self._dependents[job_id])
        while stack:
            descendant = stack.pop()
            if self.state[descendant] == "pending":
                self.state[descendant] = "blocked"
            stack.extend(self._dependents[descendant])

    def statuses(self):
        return dict(self.state)

    def done(self):
        return all(status not in ("pending", "running") for status in self.state.values())
