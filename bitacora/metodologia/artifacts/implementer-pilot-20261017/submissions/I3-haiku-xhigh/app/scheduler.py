"""Dependency-aware job scheduler with explicit start and finish calls."""
from .graph import invert_graph, validate_graph

PENDING = 'pending'
RUNNING = 'running'
SUCCEEDED = 'succeeded'
FAILED = 'failed'
BLOCKED = 'blocked'

__all__ = ['Scheduler']


def _validate_max_parallel(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f'max_parallel must be an integer, got {value!r}')
    if value < 1:
        raise ValueError(f'max_parallel must be at least 1, got {value!r}')
    return value


class Scheduler:
    """Tracks job states over a validated dependency graph.

    Jobs are never executed automatically: callers start eligible jobs and
    report each outcome with ``finish``.
    """

    def __init__(self, jobs, max_parallel=2):
        self.max_parallel = _validate_max_parallel(max_parallel)
        self.jobs = validate_graph(jobs)
        self.state = {job: PENDING for job in self.jobs}
        self._dependents = invert_graph(self.jobs)
        self._unmet = {job: len(deps) for job, deps in self.jobs.items()}
        self._ready = {job for job, count in self._unmet.items() if count == 0}
        self._running = 0

    def ready(self):
        """Return sorted IDs of every pending job whose dependencies all succeeded."""
        return sorted(self._ready)

    def start(self, job_id):
        """Move an eligible pending job to running, if capacity allows."""
        job = self._require_known(job_id)
        if job not in self._ready:
            raise ValueError(f'job {job!r} is not eligible to start')
        if self._running >= self.max_parallel:
            raise ValueError(f'no free capacity to start job {job!r}')
        self._ready.discard(job)
        self.state[job] = RUNNING
        self._running += 1

    def finish(self, job_id, success=True):
        """Record the outcome of a running job."""
        job = self._require_known(job_id)
        if self.state[job] != RUNNING:
            raise ValueError(f'job {job!r} is not running')
        self._running -= 1
        if success:
            self._mark_succeeded(job)
        else:
            self.state[job] = FAILED
            self._block_descendants(job)

    def statuses(self):
        """Return a fresh ``{job_id: state}`` dict."""
        return dict(self.state)

    def done(self):
        """Return True once no pending or running jobs remain."""
        return not any(state in (PENDING, RUNNING) for state in self.state.values())

    def _require_known(self, job_id):
        if not isinstance(job_id, str) or job_id not in self.state:
            raise ValueError(f'unknown job {job_id!r}')
        return job_id

    def _mark_succeeded(self, job):
        self.state[job] = SUCCEEDED
        for child in self._dependents[job]:
            self._unmet[child] -= 1
            if self._unmet[child] == 0:
                self._ready.add(child)

    def _block_descendants(self, failed_job):
        """Block every pending transitive dependent of ``failed_job``.

        A non-pending job has no pending descendants, so skipping it also
        bounds the walk: each job is visited at most once.
        """
        stack = list(self._dependents[failed_job])
        while stack:
            job = stack.pop()
            if self.state[job] != PENDING:
                continue
            self.state[job] = BLOCKED
            self._ready.discard(job)
            stack.extend(self._dependents[job])
