/* The phone's side of the remote contract: runtime checks of what the gateway sends, typed by the generated contract
 * (src/contract.generated.ts, from skill/scripts/bt_contracts/remote.py). Pure functions: the node tests import this
 * file directly, so it only uses erasable TypeScript. */
import { REOPENABLE_RUN_STATUSES, REOPENABLE_TASK_STATES } from "../contract.generated.ts";
import type {
  CommandHistoryItem, FailureReview, GatewaySnapshot, Precondition, QuotaAccount, RemoteEvent, RouteOption, SnapshotRun,
  SnapshotTask, TaskTarget,
} from "../contract.generated.ts";

/** A snapshot task plus what the phone remembers between polls (a reopen it sent and the Scheduler not yet showed). */
export type TaskView = SnapshotTask & { reopenedForRecovery?: boolean };
export type RunView = Omit<SnapshotRun, "tasks"> & { tasks: TaskView[] };
export type SnapshotView = Omit<GatewaySnapshot, "runs"> & { runs: RunView[] };
/** One feed row in the shape /flow's FlowCore groups. */
export type FlowEvent = { id: string; cursor: string; run: string; seq: string; ord: number; task: string; attempt: string; from: string; to: string; kind: string; summary: string; at_epoch: number };
export type FlowCore = { groupRows(events: FlowEvent[]): { ev: FlowEvent; n: number; first: number; last: number }[]; taskState(state: string): string };

type Json = Record<string, unknown>;
const record = (value: unknown): Json | null => typeof value === "object" && value !== null && !Array.isArray(value) ? value as Json : null;
const text = (value: unknown): value is string => typeof value === "string";
const list = (value: unknown): unknown[] => Array.isArray(value) ? value : [];

function fail(message: string): never { throw new Error(message); }

function checkTask(value: unknown): TaskView {
  const task = record(value);
  if (!task || !text(task.id) || !text(task.state)) fail("El snapshot contiene una tarea inválida.");
  return { ...task, history: list(task.history).filter((item) => text(record(item)?.id)) } as TaskView;
}

/** GET /api/remote/v1/snapshot and SSE `resync` frames (GatewaySnapshot). */
export function parseSnapshot(value: unknown): SnapshotView {
  const raw = record(value);
  if (!raw || raw.schemaVersion !== 1 || !text(raw.generatedAt) || !text(raw.cursor) || !Array.isArray(raw.runs) || !Array.isArray(raw.plans)) {
    fail("La respuesta del gateway no cumple el contrato de snapshot v1.");
  }
  const runs = raw.runs.map((item): RunView => {
    const run = record(item);
    if (!run || !text(run.project) || !text(run.req) || !text(run.state)) fail("El snapshot contiene una ejecución inválida.");
    return { ...run, tasks: list(run.tasks).map(checkTask) } as RunView;
  });
  for (const item of raw.plans) {
    const plan = record(item);
    if (!plan || !text(plan.project) || !text(plan.req) || !text(plan.state)) fail("El snapshot contiene un plan inválido.");
  }
  for (const item of list(raw.rounds)) {
    const round = record(item);
    if (!round || !text(round.project) || !text(round.req) || typeof round.round !== "number" || !text(round.status) || !Array.isArray(round.questions)
      || round.questions.some((question) => !text(record(question)?.id) || !text(record(question)?.text))) fail("El snapshot contiene una ronda inválida.");
  }
  for (const item of list(raw.decisionRequests)) {
    const decision = record(item);
    if (!decision || !text(decision.id) || !text(decision.project) || !text(decision.req) || !text(decision.title) || !text(decision.what)
      || !list(decision.options).length || list(decision.options).some((option) => !text(record(option)?.id) || !text(record(option)?.label))) {
      fail("La decisión no contiene opciones y consecuencias válidas.");
    }
  }
  const laptop = record(raw.laptop);
  const online = typeof laptop?.online === "boolean" ? laptop.online : raw.online !== false;
  return { ...raw, runs, rounds: list(raw.rounds), decisionRequests: list(raw.decisionRequests), laptop: { online } } as SnapshotView;
}

const ROUTES: Record<RemoteEvent["type"], [string, string, string]> = {
  "attempt.failed": ["M3", "M6", "execution_finished"], "attempt.blocked": ["M3", "M5", "incident"],
  "attempt.stalled": ["M3", "M1", "incident_detected"], "run.finished": ["M6", "owner", "execution_finished"],
  "plan.waiting": ["M6", "owner", "planning"], "round.waiting": ["M5", "owner", "recommendation"],
  "quota.exhausted": ["M2", "M1", "reservation_refused"], "laptop.offline": ["M1", "owner", "incident"],
  "command.updated": ["owner", "M1", "state_change"],
};

/** One SSE `event` frame (RemoteEvent) as a feed row; system events have no run and no row. */
export function parseFlowEvent(value: unknown): FlowEvent | null {
  const event = record(value);
  const target = record(event?.target);
  const data = record(event?.data);
  if (!event || event.schemaVersion !== 1 || !target || !data || !text(event.id) || !text(event.cursor) || !text(event.type)
    || !text(event.occurredAt) || !text(target.project) || !text(target.req)) return null;
  const route = ROUTES[event.type as RemoteEvent["type"]];
  const date = new Date(event.occurredAt);
  if (!route || Number.isNaN(date.valueOf())) return null;
  const [from, to, kind] = route;
  return { id: event.id, cursor: event.cursor, run: `${target.project}/${target.req}`, seq: event.cursor, ord: date.valueOf(),
    task: text(target.taskId) ? target.taskId : "", attempt: text(target.attemptId) ? target.attemptId : "", from, to, kind,
    summary: text(data.summary) ? data.summary : text(data.message) ? data.message : event.type, at_epoch: date.valueOf() / 1000 };
}

/** GET /api/remote/v1/quotas (QuotasResponse): every account with its list of windows (F41). */
export function parseQuotas(value: unknown): { accounts: QuotaAccount[]; checkedAt: string } {
  const body = record(value);
  if (!body || !Array.isArray(body.accounts)) fail("No se pudieron consultar las cuotas en vivo.");
  const accounts = body.accounts.flatMap((item): QuotaAccount[] => {
    const account = record(item);
    if (!account || !Array.isArray(account.windows)) return [];
    const windows = account.windows.filter((window) => text(record(window)?.window) && typeof record(window)?.usedPercent === "number");
    return [{ ...account, windows } as QuotaAccount];
  });
  return { accounts, checkedAt: text(body.checkedAt) ? body.checkedAt : "" };
}

/** GET /api/remote/v1/routes (RoutesResponse), keeping only routes a pinned retry accepts. */
export function parseRoutes(value: unknown): RouteOption[] {
  const body = record(value);
  if (!body || !Array.isArray(body.routes)) fail("No se pudieron cargar las rutas disponibles.");
  return body.routes.flatMap((item): RouteOption[] => {
    const route = record(item);
    // `route_id` is the alias window of laptops that served routes before the contract (removed in v2).
    const routeId = route ? route.routeId ?? route.route_id : undefined;
    return route && text(routeId) && text(route.provider) && text(route.model) && text(route.profile) && route.available === true
      ? [{ ...route, routeId } as RouteOption] : [];
  });
}

const SECRET = /\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|KEY|CREDENTIAL)[A-Z0-9_]*)\s*(?:=|:)\s*(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;]+)/gi;
const safe = (value: string): string => value.replace(SECRET, "$1=[REDACTED]");

/** GET /api/remote/v1/attempts/{id}/review (FailureReview), redacted once more before display. */
export function parseFailureReview(value: unknown): FailureReview {
  const review = record(value);
  const verification = record(review?.verification);
  const diff = record(review?.diff);
  if (!review || !text(review.attemptId) || !text(review.cause) || !verification || !diff || !text(review.logTail)) {
    fail("El detalle del intento no cumple el contrato v1.");
  }
  return {
    attemptId: safe(review.attemptId), cause: safe(review.cause),
    verification: { command: text(verification.command) ? safe(verification.command) : null, output: text(verification.output) ? safe(verification.output) : "" },
    diff: { stat: text(diff.stat) ? safe(diff.stat) : null, files: list(diff.files).filter(text).map(safe) },
    logTail: safe(review.logTail),
  };
}

/** GET /api/remote/v1/commands (CommandHistoryResponse). */
export function parseCommandHistory(value: unknown): CommandHistoryItem[] {
  const body = record(value);
  if (!body || !Array.isArray(body.commands)) fail("La respuesta del historial de comandos es inválida.");
  return body.commands.filter((item): item is CommandHistoryItem => {
    const row = record(item);
    return !!row && text(row.id) && text(row.command) && text(row.target) && text(row.origin) && text(row.submittedAt) && text(row.result);
  });
}

/** The reopen a blocked M1 run offers: its first reopenable task, guarded by that task's own state (F21). */
export function runReopen(run: Pick<RunView, "project" | "req" | "state" | "tasks">): { target: TaskTarget; precondition: Precondition } | null {
  if (!(REOPENABLE_RUN_STATUSES as readonly string[]).includes(run.state)) return null;
  const task = run.tasks.find((item) => (REOPENABLE_TASK_STATES as readonly string[]).includes(item.state));
  return task ? { target: { kind: "task", project: run.project, req: run.req, taskId: task.id }, precondition: taskPrecondition(task) } : null;
}

/** A task command's guard: its state, and for durable runs the sequence at which it last changed (stale views are refused). */
export function taskPrecondition(task: Pick<TaskView, "state" | "revision">): Precondition {
  return { state: task.state, ...(typeof task.revision === "number" ? { revision: task.revision } : {}) };
}
