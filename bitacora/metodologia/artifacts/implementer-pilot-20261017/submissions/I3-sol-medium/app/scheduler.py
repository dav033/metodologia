"""Explicit, single-threaded scheduling of dependency graphs."""

from .graph import validate_graph


class Scheduler:
    def __init__(self, jobs, max_parallel=2):
        if (not isinstance(max_parallel, int)
                or isinstance(max_parallel, bool) or max_parallel < 1):
            raise ValueError("max_parallel must be an integer of at least 1")
        self.jobs = validate_graph(jobs)
        self.max_parallel = max_parallel
        self.state = {job: 'pending' for job in self.jobs}
        self._dependents = {job: set() for job in self.jobs}
        for job, deps in self.jobs.items():
            for dependency in deps:
                self._dependents[dependency].add(job)

    def _eligible(self, job_id):
        return (self.state.get(job_id) == 'pending'
                and all(self.state[dep] == 'succeeded'
                        for dep in self.jobs[job_id]))

    def ready(self):
        """List all eligible pending jobs, regardless of free capacity."""
        return sorted(job for job in self.jobs if self._eligible(job))

    def start(self, job_id):
        if not self._eligible(job_id):
            raise ValueError(f"Job {job_id!r} is not ready")
        if sum(state == 'running' for state in self.state.values()) >= self.max_parallel:
            raise ValueError("No scheduling capacity available")
        self.state[job_id] = 'running'

    def finish(self, job_id, success=True):
        if self.state.get(job_id) != 'running':
            raise ValueError(f"Job {job_id!r} is not running")
        self.state[job_id] = 'succeeded' if success else 'failed'
        if not success:
            self._block_descendants(job_id)

    def _block_descendants(self, job_id):
        pending = [job_id]
        while pending:
            for dependent in self._dependents[pending.pop()]:
                if self.state[dependent] == 'pending':
                    self.state[dependent] = 'blocked'
                    pending.append(dependent)

    def statuses(self):
        return dict(self.state)

    def done(self):
        return all(state not in ('pending', 'running')
                   for state in self.state.values())
