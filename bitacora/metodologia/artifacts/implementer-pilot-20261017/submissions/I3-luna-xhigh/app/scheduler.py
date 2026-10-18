"""A single-threaded scheduler for explicitly dispatched jobs."""

from collections import deque

from .graph import validate_graph

__all__ = ["Scheduler"]


class Scheduler:
    def __init__(self, jobs, max_parallel=2):
        if isinstance(max_parallel, bool) or not isinstance(max_parallel, int) or max_parallel < 1:
            raise ValueError("max_parallel must be an integer of at least 1")

        self.jobs = validate_graph(jobs)
        self.max_parallel = max_parallel
        self.state = {job_id: "pending" for job_id in self.jobs}
        self._dependents = {job_id: [] for job_id in self.jobs}
        for job_id, dependencies in self.jobs.items():
            for dependency in dependencies:
                self._dependents[dependency].append(job_id)

    def ready(self):
        """Return every pending job whose dependencies have succeeded."""
        return sorted(
            job_id
            for job_id, dependencies in self.jobs.items()
            if self.state[job_id] == "pending"
            and all(self.state[dependency] == "succeeded" for dependency in dependencies)
        )

    def start(self, job_id):
        """Mark an eligible job as running if capacity is available."""
        if job_id not in self.state or self.state[job_id] != "pending":
            raise ValueError("job is not pending")
        if job_id not in self.ready():
            raise ValueError("job dependencies have not succeeded")
        running_count = sum(status == "running" for status in self.state.values())
        if running_count >= self.max_parallel:
            raise ValueError("maximum parallel job count reached")

        self.state[job_id] = "running"

    def finish(self, job_id, success=True):
        """Finish a running job and block pending descendants on failure."""
        if job_id not in self.state or self.state[job_id] != "running":
            raise ValueError("job is not running")

        if success:
            self.state[job_id] = "succeeded"
            return

        self.state[job_id] = "failed"
        self._block_pending_descendants(job_id)

    def _block_pending_descendants(self, job_id):
        pending = deque(self._dependents[job_id])
        visited = set()
        while pending:
            descendant = pending.popleft()
            if descendant in visited:
                continue
            visited.add(descendant)

            if self.state[descendant] == "pending":
                self.state[descendant] = "blocked"

            # Continue through running and completed jobs as well: any pending
            # jobs below them are still descendants of the failed job.
            pending.extend(self._dependents[descendant])

    def statuses(self):
        """Return a copy of the current job states."""
        return dict(self.state)

    def done(self):
        """Return whether all jobs are in terminal states."""
        return all(status not in ("pending", "running") for status in self.state.values())
