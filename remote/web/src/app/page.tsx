"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { QuotasPanel, RoutesPanel, type RouteOption } from "./recovery-panels";

type Target = { kind: "run" | "attempt" | "task" | "plan" | "round"; project: string; req: string; taskId?: string; attemptId?: string; roundId?: string };
type Run = { project: string; req: string; state: string; updatedAt?: string; lastSeenAt?: string; revision?: number; activeAttempt?: { id: string; state?: string; updatedAt?: string }; tasks?: Task[] };
type FailureReview = { attemptId: string };
type Task = { id: string; title?: string; state: string; revision?: number; updatedAt?: string; acceptanceCriteria?: string[]; activeAttempt?: { id: string; state?: string; updatedAt?: string }; reviewAttempt?: FailureReview };
type Plan = { id?: string; project: string; req: string; state: string; revision?: number; updatedAt?: string; acceptanceCriteria?: string[]; tasks?: Task[] };
type RoundQuestion = { id: string; text: string; type: "choice" | "open"; options?: { key: string; label: string }[]; recommended?: string; why?: string; suggested?: string };
type Round = { project: string; req: string; round: number; id?: string; title?: string; intro?: string; coverage?: string; status: string; revision?: number; questions: RoundQuestion[] };
type DecisionOption = { id: string; label: string; consequence: string };
type DecisionRequest = { id: string; project: string; req: string; task?: string; title: string; what: string; evidence?: string[]; options: DecisionOption[]; recommended?: string; unskippable?: boolean; state?: string; revision?: number };
type Snapshot = { schemaVersion: 1; generatedAt: string; cursor: string; runs: Run[]; plans: Plan[]; rounds?: Round[]; decisionRequests?: DecisionRequest[]; laptop?: { online: boolean; checkedAt?: string } };
type Session = { authenticated: boolean };
type CommandHistoryItem = { id: string; type: string; target: string; submittedAt: string; origin: string; result: string };
type FlowEvent = { id: string; cursor: string; run: string; seq: string; ord: number; task: string; attempt: string; from: string; to: string; kind: string; summary: string; at_epoch: number };
type FlowCore = { groupRows(events: FlowEvent[]): { ev: FlowEvent; n: number; first: number; last: number }[]; taskState(state: string): string };
declare global { interface Window { FlowCore?: FlowCore } }

function record(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function text(value: unknown): value is string { return typeof value === "string"; }
function field(source: Record<string, unknown>, camel: string, snake: string): unknown { return source[camel] ?? source[snake]; }

function parseFlowEvent(value: unknown): FlowEvent | null {
  const event = record(value);
  const target = record(event?.target);
  const data = record(event?.data);
  if (!event || event.schemaVersion !== 1 || !target || !data || !text(event.id) || !text(event.cursor) || !text(event.type) || !text(target.project) || !text(target.req) || !text(event.occurredAt)) return null;
  const task = text(field(target, "taskId", "task_id")) ? String(field(target, "taskId", "task_id")) : "";
  const attempt = text(field(target, "attemptId", "attempt_id")) ? String(field(target, "attemptId", "attempt_id")) : "";
  const routes: Record<string, [string, string, string]> = {
    "attempt.failed": ["M3", "M6", "execution_finished"], "attempt.blocked": ["M3", "M5", "incident"],
    "attempt.stalled": ["M3", "M1", "incident_detected"], "run.finished": ["M6", "owner", "execution_finished"],
    "plan.waiting": ["M6", "owner", "planning"], "round.waiting": ["M5", "owner", "recommendation"],
    "quota.exhausted": ["M2", "M1", "reservation_refused"], "laptop.offline": ["M1", "owner", "incident"],
    "command.updated": ["owner", "M1", "state_change"],
  };
  const route = routes[event.type];
  if (!route) return null;
  const [from, to, kind] = route;
  const date = new Date(event.occurredAt);
  if (Number.isNaN(date.valueOf())) return null;
  return { id: event.id, cursor: event.cursor, run: `${target.project}/${target.req}`, seq: event.cursor, ord: date.valueOf(), task,
    attempt, from, to, kind, summary: text(data.summary) ? data.summary : text(data.message) ? data.message : event.type,
    at_epoch: date.valueOf() / 1000 };
}

function parseSnapshot(value: unknown): Snapshot {
  const raw = record(value);
  const generatedAt = raw ? field(raw, "generatedAt", "generated_at") : undefined;
  if (!raw || raw.schemaVersion !== 1 || !text(generatedAt) || !text(raw.cursor) || !Array.isArray(raw.runs) || !Array.isArray(raw.plans)) {
    throw new Error("La respuesta del gateway no cumple el contrato de snapshot v1.");
  }
  const parseAttempt = (value: unknown) => {
    const attempt = record(value);
    const id = attempt && field(attempt, "id", "attempt_id");
    if (!attempt || !text(id)) return undefined;
    const state = attempt.state;
    const updatedAt = field(attempt, "updatedAt", "updated_at");
    return { id, state: text(state) ? state : undefined, updatedAt: text(updatedAt) ? updatedAt : undefined };
  };
  const parseTask = (item: unknown): Task => {
    const task = record(item);
    if (!task || !text(task.id) || !text(task.state)) throw new Error("El snapshot contiene una tarea inválida.");
    const criteria = field(task, "acceptanceCriteria", "acceptance_criteria");
    const updatedAt = field(task, "updatedAt", "updated_at");
    const review = record(field(task, "reviewAttempt", "review_attempt"));
    const attemptId = review ? (field(review, "id", "attempt_id") ?? field(review, "attemptId", "attempt_id")) : undefined;
    const reviewAttempt = review && text(attemptId) ? { attemptId } : undefined;
    return { id: task.id, title: text(task.title) ? task.title : undefined, state: task.state,
      revision: typeof task.revision === "number" ? task.revision : undefined,
      updatedAt: text(updatedAt) ? updatedAt : undefined,
      acceptanceCriteria: Array.isArray(criteria) ? criteria.filter(text) : [],
      activeAttempt: parseAttempt(field(task, "activeAttempt", "active_attempt")), reviewAttempt };
  };
  const runs = raw.runs.map((item): Run => {
    const run = record(item);
    if (!run || !text(run.project) || !text(run.req) || !text(run.state)) throw new Error("El snapshot contiene una ejecución inválida.");
    const updatedAt = field(run, "updatedAt", "updated_at");
    const lastSeenAt = field(run, "lastSeenAt", "last_seen_at");
    return { project: run.project, req: run.req, state: run.state, revision: typeof run.revision === "number" ? run.revision : undefined,
      updatedAt: text(updatedAt) ? updatedAt : undefined, lastSeenAt: text(lastSeenAt) ? lastSeenAt : undefined,
      activeAttempt: parseAttempt(field(run, "activeAttempt", "active_attempt")), tasks: Array.isArray(run.tasks) ? run.tasks.map(parseTask) : [] };
  });
  const plans = raw.plans.map((item): Plan => {
    const plan = record(item);
    if (!plan || !text(plan.project) || !text(plan.req) || !text(plan.state)) throw new Error("El snapshot contiene un plan inválido.");
    const criteria = field(plan, "acceptanceCriteria", "acceptance_criteria");
    const updatedAt = field(plan, "updatedAt", "updated_at");
    return { id: text(plan.id) ? plan.id : undefined, project: plan.project, req: plan.req, state: plan.state,
      revision: typeof plan.revision === "number" ? plan.revision : undefined,
      updatedAt: text(updatedAt) ? updatedAt : undefined,
      acceptanceCriteria: Array.isArray(criteria) ? criteria.filter(text) : [],
      tasks: Array.isArray(plan.tasks) ? plan.tasks.map(parseTask) : [] };
  });
  const rounds = Array.isArray(raw.rounds) ? raw.rounds.map((item): Round => {
    const round = record(item);
    const number = round && field(round, "round", "round_number");
    if (!round || !text(round.project) || !text(round.req) || typeof number !== "number" || !text(round.status) || !Array.isArray(round.questions)) {
      throw new Error("El snapshot contiene una ronda inválida.");
    }
    return { project: round.project, req: round.req, round: number, id: text(round.id) ? round.id : undefined,
      title: text(round.title) ? round.title : undefined, intro: text(round.intro) ? round.intro : undefined,
      coverage: text(round.coverage) ? round.coverage : undefined, status: round.status,
      revision: typeof round.revision === "number" ? round.revision : undefined,
      questions: round.questions.map((value): RoundQuestion => {
        const question = record(value);
        if (!question || !text(question.id) || !text(question.text)) throw new Error("El snapshot contiene una pregunta inválida.");
        const options = Array.isArray(question.options) ? question.options.flatMap((option) => {
          const choice = record(option);
          return choice && text(choice.key) && text(choice.label) ? [{ key: choice.key, label: choice.label }] : [];
        }) : undefined;
        return { id: question.id, text: question.text, type: question.type === "choice" || options?.length ? "choice" : "open", options,
          recommended: text(question.recommended) ? question.recommended : undefined, why: text(question.why) ? question.why : undefined,
          suggested: text(question.suggested) ? question.suggested : undefined };
      }) };
  }) : [];
  const decisionValues = Array.isArray(raw.decisionRequests) ? raw.decisionRequests : Array.isArray(raw.decision_requests) ? raw.decision_requests : [];
  const decisionRequests = decisionValues.map((value): DecisionRequest => {
    const decision = record(value);
    if (!decision || !text(decision.id) || !text(decision.project) || !text(decision.req)) throw new Error("El snapshot contiene una decisión inválida.");
    const options = Array.isArray(decision.options) ? decision.options.flatMap((option) => {
      const choice = record(option);
      return choice && text(choice.id) && text(choice.label) && text(choice.consequence) ? [{ id: choice.id, label: choice.label, consequence: choice.consequence }] : [];
    }) : [];
    if (!text(decision.title) || !text(decision.what) || options.length === 0) throw new Error("La decisión no contiene opciones y consecuencias válidas.");
    return { id: decision.id, project: decision.project, req: decision.req, task: text(decision.task) ? decision.task : undefined,
      title: decision.title, what: decision.what, evidence: Array.isArray(decision.evidence) ? decision.evidence.filter(text) : [], options,
      recommended: text(decision.recommended) ? decision.recommended : undefined,
      unskippable: typeof decision.unskippable === "boolean" ? decision.unskippable : undefined,
      state: text(decision.state) ? decision.state : undefined, revision: typeof decision.revision === "number" ? decision.revision : undefined };
  });
  const laptop = record(raw.laptop);
  const cursor = raw.cursor;
  return { schemaVersion: 1, generatedAt: String(generatedAt), cursor: String(cursor), runs, plans, rounds, decisionRequests,
    laptop: laptop && typeof laptop.online === "boolean" ? { online: laptop.online, checkedAt: text(field(laptop, "checkedAt", "checked_at")) ? String(field(laptop, "checkedAt", "checked_at")) : undefined } : undefined };
}

function prettyTime(value?: string): string {
  if (!value) return "Sin actividad registrada";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Hora no disponible" : new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export default function HomePage() {
  const [session, setSession] = useState<Session | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [feed, setFeed] = useState<FlowEvent[]>([]);
  const [error, setError] = useState("");
  const [working, setWorking] = useState("");
  const [reason, setReason] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [typedReq, setTypedReq] = useState("");
  const [commandHistory, setCommandHistory] = useState<CommandHistoryItem[]>([]);
  const [historyError, setHistoryError] = useState("");
  const snapshotRequest = useRef(0);
  const reopenedTasks = useRef(new Set<string>());

  const refreshSnapshot = useCallback(async () => {
    const request = ++snapshotRequest.current;
    const response = await fetch("/api/remote/v1/snapshot", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo cargar el estado (${response.status}).`);
    const nextSnapshot = parseSnapshot(await response.json());
    if (request === snapshotRequest.current) {
      setSnapshot({ ...nextSnapshot, runs: nextSnapshot.runs.map((run) => ({ ...run, tasks: run.tasks?.map((task) => {
        const key = `${run.project}/${run.req}/${task.id}`;
        if (reopenedTasks.current.has(key) && ["failed", "blocked", "rejected"].includes(task.state)) {
          return { ...task, state: "recovering" };
        }
        if (reopenedTasks.current.has(key)) reopenedTasks.current.delete(key);
        return task;
      }) })) });
    }
  }, []);

  const refreshCommandHistory = useCallback(async () => {
    const response = await fetch("/api/remote/v1/commands?after=&limit=100", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo cargar el historial (${response.status}).`);
    const payload: unknown = await response.json();
    const history = record(payload);
    if (!history || !Array.isArray(history.commands)) throw new Error("La respuesta del historial de comandos es inválida.");
    const rows = history.commands.flatMap((value): CommandHistoryItem[] => {
      const item = record(value);
      if (!item) return [];
      const id = field(item, "id", "idempotency_key");
      const type = text(item.command) ? item.command : item.type;
      const submittedAt = field(item, "submittedAt", "received_at");
      const targetObject = record(item.target);
      const targetLabel = text(item.target) ? item.target : targetObject && text(targetObject.project) && text(targetObject.req) ? `${targetObject.project}/${targetObject.req}` : "";
      const result = text(item.result) ? item.result : item.status;
      if (!text(id) || !text(type) || !text(submittedAt) || !text(targetLabel) || !text(item.origin) || !text(result)) return [];
      return [{ id, type, target: targetLabel, submittedAt, origin: item.origin, result }];
    });
    setCommandHistory((current) => {
      const currentById = new Map(current.map((item) => [item.id, item]));
      const merged = rows.map((row) => {
        const local = currentById.get(row.id);
        const genericRejection = row.result === "Rechazado" || row.result === "REJECTED";
        return genericRejection && local?.result.startsWith("Rechazado:") ? { ...row, result: local.result } : row;
      });
      return [...merged, ...current.filter((item) => !rows.some((row) => row.id === item.id))]
        .sort((a, b) => b.submittedAt.localeCompare(a.submittedAt)).slice(0, 100);
    });
    setHistoryError("");
  }, []);

  const load = useCallback(async () => {
    const sessionResponse = await fetch("/api/auth/session", { cache: "no-store" });
    if (sessionResponse.status === 401) { setSession({ authenticated: false }); return; }
    if (!sessionResponse.ok) throw new Error("No se pudo comprobar la sesión.");
    const sessionValue: unknown = await sessionResponse.json();
    const parsedSession = record(sessionValue);
    const authenticated = typeof parsedSession?.authenticated === "boolean"
      ? parsedSession.authenticated
      : text(parsedSession?.login) && parsedSession.login.trim().length > 0;
    if (typeof authenticated !== "boolean") throw new Error("Respuesta de sesión inválida.");
    setSession({ authenticated });
    if (!authenticated) return;
    await refreshSnapshot();
    try { await refreshCommandHistory(); }
    catch (cause) { setHistoryError(cause instanceof Error ? cause.message : "No se pudo cargar el historial."); }
  }, [refreshCommandHistory, refreshSnapshot]);

  useEffect(() => {
    void load().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Error al cargar el panel."));
  }, [load]);

  useEffect(() => {
    if (session?.authenticated !== true) return;
    let stopped = false;
    let timer = 0;
    const poll = async () => {
      try {
        await refreshSnapshot();
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel.");
      } finally {
        if (!stopped) timer = window.setTimeout(() => void poll(), 5000);
      }
    };
    timer = window.setTimeout(() => void poll(), 5000);
    return () => { stopped = true; window.clearTimeout(timer); };
<<<<<<< c0a5e47ed090adf0bb7ad5ad7bdf2c67e37ce775
  }, [session?.authenticated, refreshSnapshot]);
||||||| 03ca13926945e4dcf4ecdc4e34dddc55b76da7e1
<<<<<<< 8a050424a13d0335b6f496bee2e6edb1152be935
  }, [session?.authenticated, refreshSnapshot]);
||||||| ee57e7261a126090985dcd98194ef174bf779829
  }, [session?.authenticated, refreshSnapshot]);
||||||| b1e85c0c7e2437ff04b9fc4728f1ce154e8283d0
    const timer = window.setInterval(() => {
      void refreshSnapshot().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel."));
    }, 5000);
    return () => window.clearInterval(timer);
  }, [session?.authenticated, refreshSnapshot]);
=======
    const timer = window.setInterval(() => {
      void refreshSnapshot().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel."));
      void refreshCommandHistory().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el historial."));
    }, 5000);
    return () => window.clearInterval(timer);
  }, [session?.authenticated, refreshSnapshot, refreshCommandHistory]);
>>>>>>> 8670ff1c3a7631e9ef0b97767d36220f86a7f5ec
=======
  }, [session?.authenticated, refreshSnapshot, refreshCommandHistory]);
>>>>>>> 6ba8783aa2704a6c741fb1f93341154971cafc27
=======
  }, [session?.authenticated, refreshSnapshot, refreshCommandHistory]);
>>>>>>> ede87253b5f40c74d13b25da89f0c8ea70ac0e63

  const snapshotCursor = useRef(snapshot?.cursor);
  snapshotCursor.current = snapshot?.cursor;
  const hasSnapshotCursor = Boolean(snapshot?.cursor);
  useEffect(() => {
    const authenticated = session?.authenticated;
    if (authenticated !== true || !snapshotCursor.current) return;
    const cursor = snapshotCursor.current;
    const stream = new EventSource(`/api/remote/v1/events/stream?after=${encodeURIComponent(cursor)}`);
    stream.onmessage = (message) => {
      void refreshSnapshot().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel."));
      try {
        const event = parseFlowEvent(JSON.parse(message.data) as unknown);
        if (event) {
          setFeed((current) => current.some((item) => item.id === event.id) ? current : [...current, event].sort((a, b) => a.ord - b.ord).slice(-500));
          setError("");
        }
      } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo leer el evento remoto."); }
    };
    stream.onerror = () => setError("Se perdió la conexión en vivo; intentando reconectar…");
    return () => stream.close();
  }, [session?.authenticated, hasSnapshotCursor, refreshSnapshot]);

  async function sendCommand(event: FormEvent<HTMLFormElement>, command: Record<string, unknown>, key: string) {
    event.preventDefault();
    if (!snapshot) return;
    setWorking(key); setError("");
    const target = record(command.target);
    const targetLabel = target && text(target.project) && text(target.req) ? `${target.project}/${target.req}` : "Destino desconocido";
    const commandType = text(command.type) ? command.type : "comando";
    const submittedAt = new Date().toISOString();
    const commandId = text(command.idempotencyKey) ? command.idempotencyKey : `${key}-${submittedAt}`;
    let result = "Resultado desconocido";
    try {
      const confirmationValue = record(command.confirmation);
      if (confirmationValue && (!text(confirmationValue.challengeId) || !confirmationValue.challengeId.trim()) && text(confirmationValue.typedReq)) {
        const challengeResponse = await fetch("/api/remote/v1/challenges", { method: "POST", headers: { "content-type": "application/json", "X-Flow-Request": "1" },
          body: JSON.stringify({ target: `${text(target?.project) ? target.project : ""}/${text(target?.req) ? target.req : ""}`, typedReq: confirmationValue.typedReq }) });
        const challengeBody: unknown = await challengeResponse.json().catch(() => null);
        const challenge = record(challengeBody);
        if (!challengeResponse.ok || !text(challenge?.challengeId)) throw new Error(text(record(challengeBody)?.message) ? String(record(challengeBody)?.message) : "No se pudo obtener la confirmación del gateway.");
        command.confirmation = { challengeId: challenge.challengeId, typedReq: confirmationValue.typedReq };
      }
      const response = await fetch("/api/remote/v1/commands", { method: "POST", headers: { "content-type": "application/json", "X-Flow-Request": "1" }, body: JSON.stringify(command) });
      const payload: unknown = await response.json().catch(() => null);
      const responseRecord = record(payload);
      if (!response.ok) {
        if (responseRecord?.code === "STALE_PRECONDITION") {
          result = "Rechazado: el estado cambió";
          throw new Error("El estado cambió. Actualiza el panel antes de volver a intentarlo.");
        }
        result = "Rechazado";
        throw new Error(text(responseRecord?.message) ? responseRecord.message : `El gateway rechazó el comando (${response.status}).`);
      }
      result = text(responseRecord?.status) ? responseRecord.status : "Aceptado";
      if (commandType === "reopen" && target?.kind === "task" && text(target.project) && text(target.req) && text(target.taskId)) {
        reopenedTasks.current.add(`${target.project}/${target.req}/${target.taskId}`);
      }
      await load();
      setCommandHistory((current) => [{ id: commandId, type: commandType, target: targetLabel, submittedAt, origin: "Web", result }, ...current.filter((item) => item.id !== commandId)].slice(0, 100));
      setReason(""); setConfirmation(""); setTypedReq("");
    } catch (cause) {
      if (result.startsWith("Rechazado")) {
        setCommandHistory((current) => [{ id: commandId, type: commandType, target: targetLabel, submittedAt, origin: "Web", result }, ...current.filter((item) => item.id !== commandId)].slice(0, 100));
      }
      setError(cause instanceof Error ? cause.message : "No se pudo enviar el comando.");
    }
    finally { setWorking(""); }
  }

  function commandForm(type: string, target: Target, state: string, revision: number | undefined, key: string, extra?: Record<string, unknown>) {
    const command = (event: FormEvent<HTMLFormElement>) => {
      const formValues = new FormData(event.currentTarget);
      const typedReq = formValues.get("typedReq");
      const existingConfirmation = record(extra?.confirmation);
      const confirmation = typeof typedReq === "string" && typedReq
        ? { confirmation: { ...(existingConfirmation ?? {}), typedReq } }
        : {};
      return sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type, target,
        precondition: { state, ...(revision === undefined ? {} : { revision }) }, ...extra, ...confirmation }, key);
    };
    return command;
  }

  function roundForm(round: Round) {
    return (event: FormEvent<HTMLFormElement>) => {
      const values = new FormData(event.currentTarget);
      const answer: Record<string, unknown> = {};
      for (const question of round.questions) {
        if (question.type === "choice") answer[question.id] = { choice: String(values.get(question.id) ?? ""), note: String(values.get(`${question.id}-note`) ?? "") };
        else answer[question.id] = { text: String(values.get(question.id) ?? "") };
      }
      return sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "answer-round",
        target: { kind: "round", project: round.project, req: round.req, roundId: round.id ?? String(round.round) },
        precondition: { state: round.status, ...(round.revision === undefined ? {} : { revision: round.revision }) }, round: round.round, answer }, `${round.req}-round-${round.round}`);
    };
  }

  function decisionForm(decision: DecisionRequest, option: DecisionOption) {
    return (event: FormEvent<HTMLFormElement>) => {
      const reason = String(new FormData(event.currentTarget).get("reason") ?? "").trim();
      if (["retry_with_note", "review_pass", "review_fail"].includes(option.id) && !reason) {
        event.preventDefault(); setError("Esta opción requiere una indicación o razón."); return;
      }
      return sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "answer-decision",
        target: { kind: "run", project: decision.project, req: decision.req, ...(decision.task ? { taskId: decision.task } : {}) },
        precondition: { state: decision.state ?? "waiting", ...(decision.revision === undefined ? {} : { revision: decision.revision }) },
        requestId: decision.id, option: option.id, reason }, `${decision.req}-${decision.id}`);
    };
  }

  function retryTask(event: FormEvent<HTMLFormElement>, task: Task, run: Run, route: RouteOption) {
    const values = new FormData(event.currentTarget);
    void sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "retry",
      target: { kind: "task", project: run.project, req: run.req, taskId: task.id },
      precondition: { state: task.state, ...(task.revision === undefined ? {} : { revision: task.revision }) },
      route: { route_id: route.routeId, provider: route.provider, model: route.model, account: route.profile },
      reason: String(values.get("reason") ?? "").trim() }, `${run.req}-${task.id}-retry`);
  }

  function editBriefForm(task: Task, run: Run, plan: Plan | undefined) {
    return (event: FormEvent<HTMLFormElement>) => {
      const values = new FormData(event.currentTarget);
      const typedReq = String(values.get("typedReq") ?? "");
      void sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "edit-brief",
        target: { kind: "run", project: run.project, req: run.req, taskId: task.id },
        precondition: { state: run.state, ...((plan?.revision ?? run.revision) === undefined ? {} : { revision: plan?.revision ?? run.revision }) },
        task: task.id, field: "objective", value: String(values.get("brief") ?? "").trim(),
        confirmation: { typedReq } }, `${run.req}-${task.id}-edit-brief`);
    };
  }

  if (session === null) {
    return <main className="shell"><header className="topbar"><Link className="brand" href="/" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link></header><p className="empty" aria-live="polite">Comprobando sesión…</p></main>;
  }

  if (!session.authenticated) {
    return <main className="shell">
      <header className="topbar"><Link className="brand" href="/" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link><span className="environment">PANEL REMOTO</span></header>
      <section className="intro" aria-labelledby="welcome-title"><p className="eyebrow">OPERACIONES · EN VIVO</p><h1 id="welcome-title">Tus ejecuciones,<br /><span>siempre a mano.</span></h1><p className="lede">Inicia sesión para consultar y controlar tus ejecuciones.</p>
        <a className="sign-in" href="/api/auth/github"><svg aria-hidden="true" viewBox="0 0 24 24" width="19" height="19" fill="currentColor"><path d="M12 .9a11.1 11.1 0 0 0-3.51 21.63c.56.1.76-.24.76-.54v-2.08c-3.1.68-3.76-1.32-3.76-1.32-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 .1.85 2.06 3.42 1.45.1-.72.4-1.2.71-1.48-2.47-.28-5.07-1.24-5.07-5.51 0-1.22.44-2.21 1.16-2.99-.12-.28-.5-1.42.11-2.95 0 0 .95-.3 3.06 1.14a10.66 10.66 0 0 1 5.57 0c2.12-1.44 3.06-1.14 3.06-1.14.61 1.53.23 2.67.11 2.95.72.78 1.16 1.77 1.16 2.99 0 4.28-2.6 5.23-5.08 5.5.4.35.76 1.02.76 2.07v3.06c0 .3.2.65.77.54A11.1 11.1 0 0 0 12 .9Z" /></svg>Continuar con GitHub</a>
        <p className="security-note"><span aria-hidden="true">●</span> Acceso privado para el propietario</p>{error && <p className="error" role="alert">{error}</p>}
      </section><footer className="footer"><span>FLOW REMOTE</span><span>CONTROL PLANE · V1</span></footer>
    </main>;
  }

  const renderTask = (task: Task, run: Run) => {
    const plan = snapshot?.plans.find((item) => item.project === run.project && item.req === run.req);
    const nextRevision = (plan?.revision ?? run.revision ?? 0) + 1;
    const canRecover = task.state === "recovering";
    return <article className="task-card" key={`${run.req}-${task.id}`}>
    <div className="row-heading"><strong>{task.id}{task.title ? ` · ${task.title}` : ""}</strong><span className="state">{task.state}</span></div>
    <p className="last-seen">Última actividad · {prettyTime(task.activeAttempt?.updatedAt ?? task.updatedAt)}</p>
    {!!task.acceptanceCriteria?.length && <details><summary>Criterios de aceptación ({task.acceptanceCriteria.length})</summary><ul>{task.acceptanceCriteria.map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
    {canRecover && <RoutesPanel project={run.project} req={run.req} taskId={task.id} working={!!working}
      onRetry={(event, route) => retryTask(event, task, run, route)} />}
    {canRecover && <form className="recovery-form" onSubmit={editBriefForm(task, run, plan)}>
      <h4>Editar brief de {task.id}</h4><p className="last-seen">Creará la revisión {nextRevision}.</p>
      <label>Brief de la tarea<textarea name="brief" required maxLength={4000} defaultValue={task.title ?? ""} /></label>
      <label>Escribe {run.req} para confirmar<input name="typedReq" required autoCapitalize="characters" aria-label={`Escribe ${run.req} para confirmar la edición del brief`} /></label>
      <button disabled={!!working}>Crear revisión y actualizar tarea</button>
    </form>}
    <div className="actions">
      {(task.state === "failed" || task.state === "rejected" || task.activeAttempt?.state === "failed" || task.reviewAttempt) && <Link className="review-back feed-route" href={`/review?project=${encodeURIComponent(run.project)}&req=${encodeURIComponent(run.req)}&taskId=${encodeURIComponent(task.id)}`}>Ver intento fallido</Link>}
      {task.state === "blocked" || task.state === "failed" || task.state === "rejected" ? <form onSubmit={commandForm("reopen", { kind: "task", project: run.project, req: run.req, taskId: task.id }, task.state, task.revision, `${run.req}-${task.id}-reopen`)}><button disabled={!!working}>Reabrir</button></form> : null}
      {task.activeAttempt && <form className="cancel-form" onSubmit={commandForm("cancel-attempt", { kind: "attempt", project: run.project, req: run.req, taskId: task.id, attemptId: task.activeAttempt.id }, task.activeAttempt.state ?? task.state, task.revision, `${run.req}-${task.id}-cancel`, { reason })}><label>Motivo <input required value={reason} onChange={(event) => setReason(event.target.value)} maxLength={2000} /></label><button disabled={!!working || !reason.trim()}>Cancelar intento</button></form>}
    </div>
    </article>;
  };

  return <main className="dashboard shell">
    <header className="topbar"><Link className="brand" href="/" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link><div className="header-meta"><span className="environment">{snapshot?.laptop?.online === false ? "LAPTOP SIN CONEXIÓN" : "EN VIVO"}</span><a className="logout" href="/api/auth/logout">Salir</a></div></header>
    <section className="runs" aria-labelledby="runs-title"><div className="section-heading"><div><p className="eyebrow">CONTROL PLANE · V1</p><h1 id="runs-title">Ejecuciones</h1></div><span className="run-count">{snapshot?.runs.length ?? 0} activas</span></div>
      {error && <p className="error" role="alert">{error}</p>}
      {!snapshot ? <p className="empty">Cargando estado…</p> : snapshot.runs.length === 0 ? <p className="empty">No hay ejecuciones.</p> : <div className="run-list">{snapshot.runs.map((run) => <article className="run-card" key={`${run.project}-${run.req}`}>
        <div className="run-top"><div><p className="eyebrow">{run.project}</p><h2>{run.req}</h2></div><span className="state">{run.state}</span></div>
        <p className="last-seen">Última señal de vida · {prettyTime(run.lastSeenAt ?? run.updatedAt ?? run.activeAttempt?.updatedAt)}</p>
        {(() => {
          const activeTask = run.tasks?.find((task) => task.activeAttempt || ["running", "verifying", "dispatched"].includes(task.state));
          const activeAttempt = activeTask?.activeAttempt ?? run.activeAttempt;
          const activeModule = activeAttempt?.state === "verifying" ? "M6" : activeAttempt ? "M3" : run.state === "paused" ? "M1" : "En espera";
          return <div className="activity-strip" aria-label="Actividad actual"><span className="activity-module">{activeModule}</span><span>{activeTask ? `Tarea ${activeTask.id}` : "Sin tarea activa"}</span><span>{activeAttempt ? `Intento ${activeAttempt.id}` : "Sin intento activo"}</span></div>;
        })()}
        <div className="actions">
          {run.state === "running" ? <form onSubmit={commandForm("pause", { kind: "run", project: run.project, req: run.req }, run.state, run.revision, `${run.req}-pause`)}><button disabled={!!working}>Pausar</button></form> : null}
          {run.state === "paused" ? <form onSubmit={commandForm("resume", { kind: "run", project: run.project, req: run.req }, run.state, run.revision, `${run.req}-resume`)}><button disabled={!!working}>Reanudar</button></form> : null}
          {["failed", "rejected", "blocked", "cancelled", "finished"].includes(run.state) ? <form onSubmit={commandForm("reopen", { kind: "run", project: run.project, req: run.req }, run.state, run.revision, `${run.req}-reopen`)}><button disabled={!!working}>Reabrir ejecución</button></form> : null}
          {run.activeAttempt && !run.tasks?.some((task) => task.activeAttempt?.id === run.activeAttempt?.id) && <form className="cancel-form" onSubmit={commandForm("cancel-attempt", { kind: "attempt", project: run.project, req: run.req, attemptId: run.activeAttempt.id }, run.activeAttempt.state ?? run.state, run.revision, `${run.req}-cancel-attempt`, { reason })}><label>Motivo <input required value={reason} onChange={(event) => setReason(event.target.value)} maxLength={2000} /></label><button disabled={!!working || !reason.trim()}>Cancelar intento</button></form>}
        </div>
        {!!run.tasks?.length && <div className="task-list"><h3>Tareas</h3>{run.tasks.map((task) => renderTask(task, run))}</div>}
        <section className="feed" aria-label={`Feed ${run.req}`}><h3>Actividad reciente</h3>{(() => {
          const rows = typeof window === "undefined" ? [] : window.FlowCore?.groupRows(feed.filter((event) => event.run === `${run.project}/${run.req}`)) ?? [];
          return rows.length ? <ol>{rows.map(({ ev, n, first, last }) => <li key={ev.id}><span className="feed-route">{ev.from} → {ev.to}</span><span>{ev.summary}{n > 1 ? ` ×${n}` : ""}</span><time dateTime={new Date(last * 1000).toISOString()}>{prettyTime(new Date(last * 1000).toISOString())}{first !== last ? ` – ${prettyTime(new Date(first * 1000).toISOString())}` : ""}</time></li>)}</ol> : <p className="empty">Esperando actividad del feed en vivo.</p>;
        })()}</section>
      </article>)}</div>}
    </section>
    <QuotasPanel />
    {!!snapshot?.plans.length && <section className="runs plans" aria-labelledby="plans-title"><div className="section-heading"><div><p className="eyebrow">REVISIÓN</p><h2 id="plans-title">Planes</h2></div></div><div className="run-list">{snapshot.plans.map((plan) => {
      const target: Target = { kind: "plan", project: plan.project, req: plan.req };
      return <article className="run-card" key={`${plan.project}-${plan.req}-${plan.id ?? "plan"}`}><div className="run-top"><div><p className="eyebrow">{plan.project}</p><h3>{plan.req} · Plan</h3></div><span className="state">{plan.state}</span></div>
        <p className="last-seen">Última actividad · {prettyTime(plan.updatedAt)}</p>
        {[...(plan.acceptanceCriteria ?? []), ...(plan.tasks ?? []).flatMap((task) => task.acceptanceCriteria ?? [])].length > 0 && <details><summary>Criterios de aceptación</summary><ul>{[...(plan.acceptanceCriteria ?? []), ...(plan.tasks ?? []).flatMap((task) => task.acceptanceCriteria ?? [])].map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
        <div className="actions">
          {plan.state === "review" || plan.state === "awaiting-review" ? <form onSubmit={commandForm("approve", target, plan.state, plan.revision, `${plan.req}-approve`)}><label>Escribe {plan.req} para aprobar <input required name="typedReq" pattern={plan.req} autoCapitalize="characters" aria-label={`Escribe ${plan.req} para confirmar la aprobación`} /></label><button disabled={!!working}>Aprobar plan</button></form> : null}
          {plan.state === "approved" ? <form onSubmit={commandForm("launch", target, plan.state, plan.revision, `${plan.req}-launch`)}><label>Escribe {plan.req} para ejecutar <input required name="typedReq" pattern={plan.req} autoCapitalize="characters" aria-label={`Escribe ${plan.req} para confirmar la ejecución`} /></label><button disabled={!!working}>Ejecutar plan</button></form> : null}
          <label>Confirmación <input required aria-label="Id del reto de confirmación" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder="Id del reto" /></label><label>Escribe {plan.req} <input required aria-label={`Escribe ${plan.req}`} value={typedReq} onChange={(event) => setTypedReq(event.target.value)} /></label><form onSubmit={commandForm("cancel-plan", target, plan.state, plan.revision, `${plan.req}-cancel-plan`, { confirmation: { challengeId: confirmation, typedReq } })}><input type="hidden" name="typedReq" value={typedReq} /><button disabled={!!working || typedReq !== plan.req}>Cancelar plan</button></form>
          <form onSubmit={commandForm("delete-plan", target, plan.state, plan.revision, `${plan.req}-delete-plan`, { confirmation: { challengeId: confirmation, typedReq } })}><input type="hidden" name="typedReq" value={typedReq} /><button className="danger" disabled={!!working || typedReq !== plan.req}>Eliminar plan</button></form></div>
      </article>;
    })}</div></section>}
    {!!snapshot?.rounds?.some((round) => round.status === "open") && <section className="runs plans" aria-labelledby="rounds-title"><div className="section-heading"><div><p className="eyebrow">PREGUNTAS</p><h2 id="rounds-title">Rondas abiertas</h2></div></div><div className="run-list">{snapshot.rounds.filter((round) => round.status === "open").map((round) => <article className="run-card" key={`${round.project}-${round.req}-${round.round}`}>
      <div className="run-top"><div><p className="eyebrow">{round.project}</p><h3>{round.req} · {round.title || `Ronda ${round.round}`}</h3></div><span className="state">Ronda {round.round}</span></div>
      {round.intro && <p className="last-seen">{round.intro}</p>}{round.coverage && <p className="last-seen">Cobertura · {round.coverage}</p>}
      <form className="answer-form" onSubmit={roundForm(round)}>{round.questions.map((question) => <fieldset className="question" key={question.id}><legend>{question.text}</legend>
        {question.type === "choice" ? <div className="choice-list">{(question.options ?? []).map((option) => <label className="choice-option" key={option.key}><input type="radio" name={question.id} value={option.key} required /><span>{option.label}{question.recommended === option.key ? <em> · recomendada</em> : ""}</span></label>)}</div> : <textarea name={question.id} defaultValue={question.suggested ?? ""} required aria-label={question.text} />}
        {question.why && <p className="last-seen">{question.why}</p>}{question.type === "choice" && <label className="note-label">Nota opcional <input name={`${question.id}-note`} maxLength={2000} /></label>}
      </fieldset>)}<button disabled={!!working}>Enviar respuestas</button></form>
    </article>)}</div></section>}
    {!!snapshot?.decisionRequests?.length && <section className="runs plans" aria-labelledby="decisions-title"><div className="section-heading"><div><p className="eyebrow">DECISIONES</p><h2 id="decisions-title">Esperando tu decisión</h2></div></div><div className="run-list">{snapshot.decisionRequests.map((decision) => <article className="run-card" key={decision.id}>
      <div className="run-top"><div><p className="eyebrow">{decision.project} · {decision.req}{decision.task ? ` · ${decision.task}` : ""}</p><h3>{decision.title}</h3></div>{decision.unskippable && <span className="state">Requiere revisión</span>}</div>
      <p className="last-seen">{decision.what}</p>{!!decision.evidence?.length && <details><summary>Evidencia</summary><ul>{decision.evidence.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul></details>}
      <div className="decision-options">{decision.options.map((option) => <form className={`decision-option${decision.recommended === option.id ? " recommended" : ""}`} key={option.id} onSubmit={decisionForm(decision, option)}>
        <h4>{option.label}{decision.recommended === option.id ? <span> · recomendada</span> : ""}</h4><p>{option.consequence}</p>
        {["retry_with_note", "review_pass", "review_fail"].includes(option.id) && <label className="note-label">Indicación o razón <textarea name="reason" required maxLength={2000} /></label>}
        <button disabled={!!working}>Elegir esta opción</button>
      </form>)}</div>
    </article>)}</div></section>}
    <section className="runs history" aria-labelledby="command-history-title"><div className="section-heading"><div><p className="eyebrow">TRAZABILIDAD</p><h2 id="command-history-title">Historial de comandos</h2></div></div>{historyError && <p className="error" role="status">{historyError}</p>}{commandHistory.length ? <ol className="command-history">{commandHistory.map((item) => <li key={item.id}><strong>{item.type}</strong><span>{item.target}</span><time dateTime={item.submittedAt}>{prettyTime(item.submittedAt)}</time><span>Origen · {item.origin}</span><span>Resultado · {item.result}</span></li>)}</ol> : <p className="empty">Aún no se han enviado comandos desde este panel.</p>}</section>
    <footer className="footer"><span>FLOW REMOTE</span><span>Actualizado · {prettyTime(snapshot?.generatedAt)}</span></footer>
  </main>;
}
