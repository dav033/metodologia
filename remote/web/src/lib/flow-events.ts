export type FlowEvent = {
  id: string;
  cursor: string;
  run: string;
  seq: string;
  ord: number;
  task: string;
  attempt: string;
  from: string;
  to: string;
  kind: string;
  summary: string;
  at_epoch: number;
};

type RecordValue = Record<string, unknown>;

function record(value: unknown): RecordValue | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as RecordValue : null;
}

function text(value: unknown): value is string {
  return typeof value === "string";
}

function field(source: RecordValue, camel: string, snake: string): unknown {
  return source[camel] ?? source[snake];
}

export function parseFlowEvent(value: unknown): FlowEvent | null {
  const event = record(value);
  const target = record(event?.target);
  const data = record(event?.data);
  if (!event || event.schemaVersion !== 1 || !target || !data || !text(event.id) || !text(event.cursor) ||
      !text(event.type) || !text(target.project) || !text(target.req) || !text(event.occurredAt)) return null;
  const taskId = field(target, "taskId", "task_id");
  const attemptId = field(target, "attemptId", "attempt_id");
  const task = text(taskId) ? taskId : "";
  const attempt = text(attemptId) ? attemptId : "";
  const routes: Record<string, [string, string, string]> = {
    "attempt.failed": ["M3", "M6", "execution_finished"], "attempt.blocked": ["M3", "M5", "incident"],
    "attempt.stalled": ["M3", "M1", "incident_detected"], "run.finished": ["M6", "owner", "execution_finished"],
    "plan.waiting": ["M6", "owner", "planning"], "round.waiting": ["M5", "owner", "recommendation"],
    "quota.exhausted": ["M2", "M1", "reservation_refused"], "laptop.offline": ["M1", "owner", "incident"],
    "task.progress": ["M1", "owner", "state_change"], "task.completed": ["M6", "owner", "execution_finished"],
    "command.updated": ["owner", "M1", "state_change"],
  };
  const route = routes[event.type];
  if (!route) return null;
  const [from, to, kind] = route;
  const date = new Date(event.occurredAt);
  if (Number.isNaN(date.valueOf())) return null;
  return { id: event.id, cursor: event.cursor, run: `${target.project}/${target.req}`, seq: event.cursor,
    ord: date.valueOf(), task, attempt, from, to, kind,
    summary: text(data.summary) ? data.summary : text(data.message) ? data.message : event.type,
    at_epoch: date.valueOf() / 1000 };
}
