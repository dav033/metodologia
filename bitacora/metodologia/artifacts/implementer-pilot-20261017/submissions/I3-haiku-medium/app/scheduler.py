"""Explicit, single-threaded dependency scheduler.

Callers drive the lifecycle: ``start`` a ready job, then ``finish`` it. The
scheduler never executes jobs itself.
"""
from .graph import dependents_of, validate_graph

PENDING = "pending"
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"
BLOCKED = "blocked"

_TERMINAL_STATES = frozenset((SUCCEEDED, FAILED, BLOCKED))


def _validate_max_parallel(value):
    """Require a true integer (not bool) that is at least 1."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"max_parallel must be an integer, got {value!r}")
    if value < 1:
        raise ValueError(f"max_parallel must be at least 1, got {value!r}")
    return value


class Scheduler:
    """Tracks job states over a validated dependency graph."""

    def __init__(self, jobs, max_parallel=2):
        self.max_parallel = _validate_max_parallel(max_parallel)
        self.jobs = validate_graph(jobs)
        self.state = {job_id: PENDING for job_id in self.jobs}
        self._dependents = dependents_of(self.jobs)
        self._running_count = 0

    def ready(self):
        """Return all currently eligible pending job IDs, sorted. No state change."""
        return [job_id for job_id in sorted(self.jobs) if self._is_eligible(job_id)]

    def start(self, job_id):
        """Move an eligible pending job to running if capacity allows."""
        if not self._is_eligible(job_id):
            raise ValueError(f"job {job_id!r} is not ready to start")
        if self._running_count >= self.max_parallel:
            raise ValueError(
                f"cannot start job {job_id!r}: max_parallel={self.max_parallel} reached"
            )
        self.state[job_id] = RUNNING
        self._running_count += 1

    def finish(self, job_id, success=True):
        """Record the outcome of a running job; failure blocks pending descendants."""
        if self.state.get(job_id) != RUNNING:
            raise ValueError(f"job {job_id!r} is not running")
        self._running_count -= 1
        if success:
            self.state[job_id] = SUCCEEDED
        else:
            self.state[job_id] = FAILED
            self._block_descendants(job_id)

    def statuses(self):
        """Return a fresh ``{job_id: state}`` dict."""
        return dict(self.state)

    def done(self):
        """True when no job is pending or running; blocked jobs are terminal."""
        return all(state in _TERMINAL_STATES for state in self.state.values())

    def _is_eligible(self, job_id):
        """A job is eligible when it is pending and every dependency succeeded."""
        return self.state.get(job_id) == PENDING and all(
            self.state[dep] == SUCCEEDED for dep in self.jobs[job_id]
        )

    def _block_descendants(self, failed_job_id):
        """Iteratively mark every still-pending transitive dependent as blocked."""
        stack = list(self._dependents[failed_job_id])
        while stack:
            child = stack.pop()
            if self.state[child] != PENDING:
                continue
            self.state[child] = BLOCKED
            stack.extend(self._dependents[child])
