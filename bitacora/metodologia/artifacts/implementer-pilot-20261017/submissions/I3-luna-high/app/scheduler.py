"""Explicit, single-threaded dependency job scheduler."""

from .graph import validate_graph


class Scheduler:
    """Track job eligibility and completion without executing jobs itself."""

    def __init__(self, jobs, max_parallel=2):
        if isinstance(max_parallel, bool) or not isinstance(max_parallel, int):
            raise ValueError("max_parallel must be an integer")
        if max_parallel < 1:
            raise ValueError("max_parallel must be at least 1")

        self.jobs = validate_graph(jobs)
        self.max_parallel = max_parallel
        self.state = {job_id: "pending" for job_id in self.jobs}
        self._dependents = {job_id: [] for job_id in self.jobs}
        for job_id, dependencies in self.jobs.items():
            for dependency in dependencies:
                self._dependents[dependency].append(job_id)

    def ready(self):
        """Return all pending jobs whose dependencies have succeeded."""
        return sorted(
            job_id
            for job_id, dependencies in self.jobs.items()
            if self.state[job_id] == "pending"
            and all(self.state[dependency] == "succeeded" for dependency in dependencies)
        )

    def start(self, job_id):
        """Mark an eligible job running when capacity is available."""
        if (
            job_id not in self.state
            or self.state[job_id] != "pending"
            or self._running_count() >= self.max_parallel
            or any(self.state[dependency] != "succeeded" for dependency in self.jobs[job_id])
        ):
            raise ValueError("job cannot be started")
        self.state[job_id] = "running"

    def finish(self, job_id, success=True):
        """Finish a running job and propagate failure blocking if necessary."""
        if job_id not in self.state or self.state[job_id] != "running":
            raise ValueError("job is not running")

        if success:
            self.state[job_id] = "succeeded"
            return

        self.state[job_id] = "failed"
        self._block_pending_descendants(job_id)

    def statuses(self):
        """Return a fresh mapping of job IDs to their current states."""
        return dict(self.state)

    def done(self):
        """Return whether no jobs remain pending or running."""
        return not any(state in ("pending", "running") for state in self.state.values())

    def _running_count(self):
        return sum(state == "running" for state in self.state.values())

    def _block_pending_descendants(self, failed_job):
        # Traverse the full descendant closure, but only change pending jobs.
        # Traversal continues through every node so already-terminal or running
        # nodes cannot hide pending descendants.
        stack = list(self._dependents[failed_job])
        visited = set()
        while stack:
            job_id = stack.pop()
            if job_id in visited:
                continue
            visited.add(job_id)
            if self.state[job_id] == "pending":
                self.state[job_id] = "blocked"
            stack.extend(self._dependents[job_id])


__all__ = ["Scheduler"]
