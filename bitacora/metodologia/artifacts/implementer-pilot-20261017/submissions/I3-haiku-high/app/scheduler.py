"""Dependency-aware job scheduler.

Callers explicitly ``start`` eligible jobs and ``finish`` running ones; the
scheduler never executes anything itself. Calls are expected to be
single-threaded.
"""
from .graph import dependents_of, validate_graph

PENDING = 'pending'
RUNNING = 'running'
SUCCEEDED = 'succeeded'
FAILED = 'failed'
BLOCKED = 'blocked'


def _validate_max_parallel(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError('max_parallel must be an integer')
    if value < 1:
        raise ValueError('max_parallel must be at least 1')
    return value


class Scheduler:
    """Tracks job states over a validated dependency graph.

    Attributes:
        max_parallel: maximum number of jobs that may be running at once.
        jobs: validated snapshot ``{job_id: set(dependency_ids)}``.
        state: current ``{job_id: state}`` mapping (internal; use ``statuses()``).
    """

    def __init__(self, jobs, max_parallel=2):
        self.max_parallel = _validate_max_parallel(max_parallel)
        self.jobs = validate_graph(jobs)
        self.state = {job: PENDING for job in self.jobs}
        self._dependents = dependents_of(self.jobs)
        # Number of dependencies not yet succeeded, per job.
        self._unmet = {job: len(deps) for job, deps in self.jobs.items()}
        # Pending jobs whose dependencies have all succeeded.
        self._ready = {job for job, count in self._unmet.items() if count == 0}
        self._running = 0

    def ready(self):
        """Return all currently eligible pending job IDs, sorted. Read-only."""
        return sorted(self._ready)

    def start(self, job_id):
        """Move an eligible pending job to running, if capacity allows."""
        self._require_known(job_id)
        if job_id not in self._ready:
            raise ValueError(f'job {job_id!r} is not eligible to start (state: {self.state[job_id]})')
        if self._running >= self.max_parallel:
            raise ValueError(f'no free capacity: {self._running} of {self.max_parallel} slots in use')
        self._ready.discard(job_id)
        self.state[job_id] = RUNNING
        self._running += 1

    def finish(self, job_id, success=True):
        """Record the outcome of a running job."""
        self._require_known(job_id)
        if self.state[job_id] != RUNNING:
            raise ValueError(f'job {job_id!r} is not running (state: {self.state[job_id]})')
        self._running -= 1
        if success:
            self._on_succeeded(job_id)
        else:
            self._on_failed(job_id)

    def statuses(self):
        """Return a fresh ``{job_id: state}`` dict."""
        return dict(self.state)

    def done(self):
        """True when no job is pending or running; blocked jobs are terminal."""
        return all(state not in (PENDING, RUNNING) for state in self.state.values())

    def _require_known(self, job_id):
        if not isinstance(job_id, str) or job_id not in self.state:
            raise ValueError(f'unknown job: {job_id!r}')

    def _on_succeeded(self, job_id):
        self.state[job_id] = SUCCEEDED
        for dependent in self._dependents[job_id]:
            if self.state[dependent] != PENDING:
                continue
            self._unmet[dependent] -= 1
            if self._unmet[dependent] == 0:
                self._ready.add(dependent)

    def _on_failed(self, job_id):
        self.state[job_id] = FAILED
        # Block every pending descendant. Non-pending descendants are already
        # terminal and have had their own descendants handled, so skip them.
        stack = list(self._dependents[job_id])
        while stack:
            job = stack.pop()
            if self.state[job] != PENDING:
                continue
            self.state[job] = BLOCKED
            self._ready.discard(job)
            stack.extend(self._dependents[job])
