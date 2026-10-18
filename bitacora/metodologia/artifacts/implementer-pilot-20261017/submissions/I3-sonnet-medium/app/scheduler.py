from .graph import build_dependents, validate_graph

PENDING, RUNNING, SUCCEEDED, FAILED, BLOCKED = (
    "pending", "running", "succeeded", "failed", "blocked")


class Scheduler:
    def __init__(self, jobs, max_parallel=2):
        if isinstance(max_parallel, bool) or not isinstance(max_parallel, int) or max_parallel < 1:
            raise ValueError("max_parallel must be an integer >= 1")
        self.jobs = validate_graph(jobs)
        self._dependents = build_dependents(self.jobs)
        self.max_parallel = max_parallel
        self.state = {job: PENDING for job in self.jobs}
        self._running = 0

    def _eligible(self, job):
        return self.state[job] == PENDING and all(
            self.state[d] == SUCCEEDED for d in self.jobs[job])

    def ready(self):
        return sorted(j for j in self.jobs if self._eligible(j))

    def start(self, job_id):
        if job_id not in self.state or not self._eligible(job_id):
            raise ValueError(f"job {job_id!r} is not ready")
        if self._running >= self.max_parallel:
            raise ValueError("max_parallel limit reached")
        self.state[job_id] = RUNNING
        self._running += 1

    def finish(self, job_id, success=True):
        if self.state.get(job_id) != RUNNING:
            raise ValueError(f"job {job_id!r} is not running")
        self._running -= 1
        if success:
            self.state[job_id] = SUCCEEDED
            return
        self.state[job_id] = FAILED
        stack = [job_id]
        while stack:
            for child in self._dependents[stack.pop()]:
                if self.state[child] == PENDING:
                    self.state[child] = BLOCKED
                    stack.append(child)

    def statuses(self):
        return dict(self.state)

    def done(self):
        return not any(s in (PENDING, RUNNING) for s in self.state.values())
