// Parsers for what the gateway really serves: the laptop snapshot with every key camel-cased by the gateway
// (`reqId`, `lastSignOfLife`, `planStatus`…). Snake-case spellings are still read so a cached payload keeps working.

export type Attempt = { id: string; state?: string; updatedAt?: string; failure?: string };
export type Task = { id: string; title?: string; state: string; revision?: number; updatedAt?: string; acceptanceCriteria?: string[]; activeAttempt?: Attempt; history?: Attempt[] };
export type Run = { project: string; req: string; state: string; updatedAt?: string; lastSeenAt?: string; revision?: number; activeAttempt?: Attempt; tasks?: Task[] };
export type DecisionOption = { id: string; label: string; consequence: string };
export type Decision = { id: string; task: string; title: string; what: string; reason: string; evidence: string[]; options: DecisionOption[]; recommended?: string; unskippable: boolean };
export type RoundQuestion = { id: string; text: string; type: "choice" | "open"; options: { key: string; label: string }[]; recommended?: string; why?: string; suggested?: string };
export type Round = { round: number; title: string; intro: string; questions: RoundQuestion[] };
export type Plan = { commandState?: string; project: string; req: string; title?: string; state: string; runState?: string; active: boolean; progress?: { done: number; total: number }; updatedAt?: string; decisions: Decision[]; rounds: Round[] };
export type Snapshot = { schemaVersion: 1; generatedAt: string; cursor: string; runs: Run[]; plans: Plan[]; laptopStatus?: string };

export function record(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}
export function text(value: unknown): value is string { return typeof value === "string"; }
export function field(source: Record<string, unknown>, camel: string, snake: string): unknown { return source[camel] ?? source[snake]; }
const strings = (value: unknown): string[] => Array.isArray(value) ? value.filter(text) : [];
const optional = (value: unknown): string | undefined => text(value) ? value : undefined;

function parseAttempt(value: unknown): Attempt | undefined {
  const attempt = record(value);
  const id = attempt && attempt.id;
  if (!attempt || !text(id)) return undefined;
  return { id, state: optional(attempt.state), updatedAt: optional(field(attempt, "lastActivityAt", "last_activity_at") ?? attempt.updatedAt), failure: optional(attempt.failure) };
}

function parseTask(item: unknown): Task {
  const task = record(item);
  if (!task || !text(task.id) || !text(task.state)) throw new Error("El snapshot contiene una tarea inválida.");
  return { id: task.id, title: optional(task.title), state: task.state, revision: typeof task.revision === "number" ? task.revision : undefined,
    updatedAt: optional(field(task, "updatedAt", "updated_at")), acceptanceCriteria: strings(field(task, "acceptanceCriteria", "acceptance_criteria")),
    activeAttempt: parseAttempt(task.attempt) ?? parseAttempt(field(task, "activeAttempt", "active_attempt")),
    history: Array.isArray(task.history) ? task.history.map(parseAttempt).filter((attempt): attempt is Attempt => Boolean(attempt)) : [] };
}

function parseRun(item: unknown): Run {
  const run = record(item);
  const req = run && field(run, "reqId", "req_id");
  const state = run && (run.status ?? run.state);
  if (!run || !text(run.project) || !text(req) || !text(state)) throw new Error("El snapshot contiene una ejecución inválida.");
  const tasks = Array.isArray(run.tasks) ? run.tasks.map(parseTask) : [];
  return { project: run.project, req, state, revision: typeof run.revision === "number" ? run.revision : undefined,
    updatedAt: optional(field(run, "updatedAt", "updated_at")), lastSeenAt: optional(field(run, "lastSignOfLife", "last_sign_of_life")),
    activeAttempt: tasks.find((task) => task.activeAttempt)?.activeAttempt ?? parseAttempt(field(run, "activeAttempt", "active_attempt")), tasks };
}

function parseDecision(item: unknown): Decision | null {
  const decision = record(item);
  if (!decision || !text(decision.id) || !Array.isArray(decision.options)) return null;
  const options = decision.options.flatMap((value): DecisionOption[] => {
    const option = record(value);
    return option && text(option.id) ? [{ id: option.id, label: text(option.label) ? option.label : option.id, consequence: text(option.consequence) ? option.consequence : "" }] : [];
  });
  if (!options.length) return null;
  return { id: decision.id, task: text(decision.task) ? decision.task : "", title: text(decision.title) ? decision.title : decision.id,
    what: text(decision.what) ? decision.what : "", reason: text(decision.reason) ? decision.reason : "", evidence: strings(decision.evidence),
    options, recommended: optional(decision.recommended), unskippable: decision.unskippable === true };
}

function parseRound(item: unknown): Round | null {
  const round = record(item);
  if (!round || typeof round.round !== "number" || !Array.isArray(round.questions)) return null;
  const questions = round.questions.flatMap((value): RoundQuestion[] => {
    const question = record(value);
    if (!question || !text(question.id) || !text(question.text)) return [];
    const options = Array.isArray(question.options) ? question.options.flatMap((entry) => {
      const option = record(entry);
      return option && text(option.key) ? [{ key: option.key, label: text(option.label) ? option.label : option.key }] : [];
    }) : [];
    return [{ id: question.id, text: question.text, type: question.type === "choice" || (question.type === undefined && options.length) ? "choice" : "open",
      options, recommended: optional(question.recommended), why: optional(question.why), suggested: optional(question.suggested) }];
  });
  return { round: round.round, title: text(round.title) ? round.title : `Ronda ${round.round}`, intro: text(round.intro) ? round.intro : "", questions };
}

function parsePlan(item: unknown): Plan {
  const plan = record(item);
  const req = plan && field(plan, "reqId", "req_id");
  const state = plan && (field(plan, "planStatus", "plan_status") ?? plan.status ?? plan.state);
  if (!plan || !text(plan.project) || !text(req) || !text(state)) throw new Error("El snapshot contiene un plan inválido.");
  const progress = record(plan.progress);
  return { project: plan.project, req, title: optional(plan.title), state, runState: optional(field(plan, "runStatus", "run_status")), active: plan.active === true,
    progress: progress && typeof progress.done === "number" && typeof progress.total === "number" ? { done: progress.done, total: progress.total } : undefined,
    updatedAt: optional(field(plan, "updatedAt", "updated_at")), commandState: optional(field(plan, "commandState", "command_state")),
    decisions: Array.isArray(plan.decisions) ? plan.decisions.map(parseDecision).filter((value): value is Decision => value !== null) : [],
    rounds: Array.isArray(plan.rounds) ? plan.rounds.map(parseRound).filter((value): value is Round => value !== null) : [] };
}

export function parseSnapshot(value: unknown): Snapshot {
  const raw = record(value);
  const generatedAt = raw ? field(raw, "generatedAt", "generated_at") : undefined;
  if (!raw || raw.schemaVersion !== 1 || !text(generatedAt) || !text(raw.cursor) || !Array.isArray(raw.runs) || !Array.isArray(raw.plans)) {
    throw new Error("La respuesta del gateway no cumple el contrato de snapshot v1.");
  }
  return { schemaVersion: 1, generatedAt, cursor: raw.cursor, runs: raw.runs.map(parseRun), plans: raw.plans.map(parsePlan), laptopStatus: optional(raw.laptopStatus) };
}
