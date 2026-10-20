"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { FlowEvent, parseFlowEvent } from "../lib/flow-events";
import { postRemoteMutation } from "../lib/remote-api";

type Target = { kind: "run" | "attempt" | "task" | "plan" | "round"; project: string; req: string; taskId?: string; attemptId?: string; roundId?: string };
type Run = { project: string; req: string; state: string; updatedAt?: string; lastSeenAt?: string; revision?: number; activeAttempt?: { id: string; state?: string; updatedAt?: string }; tasks?: Task[] };
type Task = { id: string; title?: string; state: string; revision?: number; updatedAt?: string; acceptanceCriteria?: string[]; activeAttempt?: { id: string; state?: string; updatedAt?: string }; reviewAttempt?: { id: string; state?: string; updatedAt?: string } };
type Plan = { id?: string; project: string; req: string; state: string; revision?: number; updatedAt?: string; acceptanceCriteria?: string[]; tasks?: Task[] };
type RoundQuestion = { id: string; text: string; type: "choice" | "open"; options?: { key: string; label: string }[]; recommended?: string; why?: string; suggested?: string };
type Round = { project: string; req: string; round: number; id?: string; title?: string; intro?: string; coverage?: string; status: string; revision?: number; questions: RoundQuestion[] };
type DecisionOption = { id: string; label: string; consequence: string };
type DecisionRequest = { id: string; project: string; req: string; task?: string; title: string; what: string; evidence?: string[]; options: DecisionOption[]; recommended?: string; unskippable?: boolean; state?: string; revision?: number };
type Snapshot = { schemaVersion: 1; generatedAt: string; cursor: string; runs: Run[]; plans: Plan[]; rounds?: Round[]; decisionRequests?: DecisionRequest[]; decisions?: DecisionRequest[]; laptop?: { online: boolean; checkedAt?: string } };
type QuotaWindow = { name: string; remaining?: number; limit?: number; resetsAt?: string; resetAt?: string };
type QuotaAccount = { id: string; windows: QuotaWindow[]; checkedAt?: string; source?: string };
type AvailableRoute = { id: string; label?: string };
type Session = { authenticated: boolean };
type CommandHistoryItem = { id: string; at: string; origin: string; result: string };
type FailureReview = {
  attemptId: string;
  cause: string;
  verification: { command: string | null; output: string };
  diff: { stat: string | null; files: string[] };
  logTail: string;
};
type FlowCore = { groupRows(events: FlowEvent[]): { ev: FlowEvent; n: number; first: number; last: number }[]; taskState(state: string): string };
declare global { interface Window { FlowCore?: FlowCore } }

function record(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function text(value: unknown): value is string { return typeof value === "string"; }
function field(source: Record<string, unknown>, camel: string, snake: string): unknown { return source[camel] ?? source[snake]; }

function safeReviewText(value: string): string {
  return value.replace(/\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|KEY|CREDENTIAL)[A-Z0-9_]*)\s*(?:=|:)\s*(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;]+)/gi, "$1=[REDACTED]");
}

function parseFailureReview(value: unknown): FailureReview {
  const review = record(value);
  const verification = record(review?.verification);
  const diff = record(review?.diff);
  if (!review || !text(review.attemptId) || !text(review.cause) || !verification || !diff || !text(review.logTail)) {
    throw new Error("El detalle del intento no cumple el contrato v1.");
  }
  const files = Array.isArray(diff.files) ? diff.files.filter(text).map(safeReviewText) : [];
  return {
    attemptId: safeReviewText(review.attemptId),
    cause: safeReviewText(review.cause),
    verification: {
      command: text(verification.command) ? safeReviewText(verification.command) : null,
      output: text(verification.output) ? safeReviewText(verification.output) : "",
    },
    diff: { stat: text(diff.stat) ? safeReviewText(diff.stat) : null, files },
    logTail: safeReviewText(review.logTail),
  };
}

function FailureReviewPanel({ attemptId }: { attemptId: string }) {
  const [review, setReview] = useState<FailureReview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void fetch(`/api/remote/v1/attempts/${encodeURIComponent(attemptId)}/review`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("No se pudo cargar la revisión del intento.");
        return parseFailureReview(await response.json() as unknown);
      })
      .then((result) => { if (active) setReview(result); })
      .catch((cause: unknown) => { if (active) setError(cause instanceof Error ? cause.message : "No se pudo cargar la revisión del intento."); });
    return () => { active = false; };
  }, [attemptId]);

  if (error) return <p className="error" role="alert">{error}</p>;
  if (!review) return <p className="empty">Cargando revisión del intento…</p>;
  return <section className="failure-review" aria-label={`Revisión del intento ${review.attemptId}`}>
    <h4>Revisión del intento {review.attemptId}</h4>
    <section className="failure-section"><h5>Causa</h5><p>{review.cause}</p></section>
    <section className="failure-section"><h5>Verificación</h5>{review.verification.command && <p className="review-command">{review.verification.command}</p>}<pre className="review-scroll">{review.verification.output || "Sin salida de verificación."}</pre></section>
    <section className="failure-section"><h5>Diff stat</h5><p>{review.diff.stat ?? "Sin diff disponible."}</p>{review.diff.files.length > 0 && <ul>{review.diff.files.map((file, index) => <li key={`${file}-${index}`}>{file}</li>)}</ul>}</section>
    <section className="failure-section"><h5>Log del agente</h5><pre className="review-scroll">{review.logTail || "Sin log disponible."}</pre></section>
  </section>;
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
    return { id: task.id, title: text(task.title) ? task.title : undefined, state: task.state,
      revision: typeof task.revision === "number" ? task.revision : undefined,
      updatedAt: text(updatedAt) ? updatedAt : undefined,
      acceptanceCriteria: Array.isArray(criteria) ? criteria.filter(text) : [],
      activeAttempt: parseAttempt(field(task, "activeAttempt", "active_attempt")),
      reviewAttempt: parseAttempt(field(task, "reviewAttempt", "review_attempt")) };
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
    const questions = round?.questions;
    if (!round || !text(round.project) || !text(round.req) || typeof number !== "number" || !text(round.status) || !Array.isArray(questions)) {
      throw new Error("El snapshot contiene una ronda inválida.");
    }
    return { project: round.project, req: round.req, round: number, id: text(round.id) ? round.id : undefined,
      title: text(round.title) ? round.title : undefined, intro: text(round.intro) ? round.intro : undefined,
      coverage: text(round.coverage) ? round.coverage : undefined, status: round.status,
      revision: typeof round.revision === "number" ? round.revision : undefined,
      questions: questions.map((value): RoundQuestion => {
        const question = record(value);
        if (!question || !text(question.id) || !text(question.text)) throw new Error("El snapshot contiene una pregunta inválida.");
        const options = Array.isArray(question.options) ? question.options.flatMap((option) => {
          const item = record(option);
          return item && text(item.key) && text(item.label) ? [{ key: item.key, label: item.label }] : [];
        }) : undefined;
        return { id: question.id, text: question.text, type: question.type === "choice" || options?.length ? "choice" : "open", options,
          recommended: text(question.recommended) ? question.recommended : undefined, why: text(question.why) ? question.why : undefined,
          suggested: text(question.suggested) ? question.suggested : undefined };
      }) };
  }) : [];
  const decisionsRaw = Array.isArray(raw.decisionRequests) ? raw.decisionRequests : Array.isArray(raw.decision_requests) ? raw.decision_requests : Array.isArray(raw.decisions) ? raw.decisions : [];
  const decisionRequests = decisionsRaw.map((value): DecisionRequest => {
    const decision = record(value);
    if (!decision || !text(decision.id) || !text(decision.project) || !text(decision.req)) throw new Error("El snapshot contiene una decisión inválida.");
    const options = Array.isArray(decision.options) ? decision.options.flatMap((option) => {
      const item = record(option);
      return item && text(item.id) && text(item.label) && text(item.consequence) ? [{ id: item.id, label: item.label, consequence: item.consequence }] : [];
    }) : [];
    if (!text(decision.title) || !text(decision.what) || options.length === 0) throw new Error("La decisión no contiene opciones y consecuencias válidas.");
    const evidence = Array.isArray(decision.evidence) ? decision.evidence.filter(text) : [];
    return { id: decision.id, project: decision.project, req: decision.req, task: text(decision.task) ? decision.task : undefined,
      title: decision.title, what: decision.what, evidence, options, recommended: text(decision.recommended) ? decision.recommended : undefined,
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
  const [commandHistory, setCommandHistory] = useState<CommandHistoryItem[]>([]);
  const [quotas, setQuotas] = useState<QuotaAccount[]>([]);
  const [availableRoutes, setAvailableRoutes] = useState<AvailableRoute[]>([]);

  const refreshSnapshot = useCallback(async () => {
    const response = await fetch("/api/remote/v1/snapshot", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo cargar el estado (${response.status}).`);
    const value: unknown = await response.json();
    setSnapshot(parseSnapshot(value));
    const raw = record(value);
    const routes = raw && Array.isArray(raw.availableRoutes) ? raw.availableRoutes : raw && Array.isArray(raw.available_routes) ? raw.available_routes : [];
    setAvailableRoutes(routes.flatMap((item) => {
      const route = record(item);
      return route && text(route.id) ? [{ id: route.id, label: text(route.label) ? route.label : route.id }] : [];
    }));
  }, []);

  const refreshQuotas = useCallback(async () => {
    const response = await fetch("/api/remote/v1/quotas", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudieron cargar las cuotas (${response.status}).`);
    const value: unknown = await response.json();
    const raw = record(value);
    if (!raw || !Array.isArray(raw.accounts)) throw new Error("La respuesta de cuotas no cumple el contrato v1.");
    setQuotas(raw.accounts.flatMap((item) => {
      const account = record(item);
      if (!account || !text(account.id)) return [];
      const windows = Array.isArray(account.windows) ? account.windows.flatMap((item) => {
        const window = record(item);
        if (!window || !text(window.name)) return [];
        return [{ name: window.name, remaining: typeof window.remaining === "number" ? window.remaining : undefined,
          limit: typeof window.limit === "number" ? window.limit : undefined,
          resetsAt: text(window.resetsAt) ? window.resetsAt : text(window.resetAt) ? window.resetAt : undefined }];
      }) : [];
      return [{ id: account.id, windows, checkedAt: text(account.checkedAt) ? account.checkedAt : undefined, source: text(account.source) ? account.source : undefined }];
    }));
  }, []);

  const refreshHistory = useCallback(async () => {
    const response = await fetch("/api/remote/v1/history", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo cargar el historial (${response.status}).`);
    const raw = record(await response.json() as unknown);
    if (!raw || !Array.isArray(raw.commands)) throw new Error("La respuesta del historial no cumple el contrato v1.");
    setCommandHistory(raw.commands.flatMap((item) => {
      const entry = record(item);
      if (!entry || !text(entry.id) || !text(entry.at)) return [];
      const label = [entry.command, entry.target].filter(text).join(" ");
      const result = text(entry.result) ? entry.result : "Sin resultado";
      return [{ id: entry.id, at: entry.at, origin: text(entry.origin) ? entry.origin : "web", result: label ? `${label} · ${result}` : result }];
    }));
  }, []);

  const load = useCallback(async () => {
    const sessionResponse = await fetch("/api/auth/session", { cache: "no-store" });
    if (sessionResponse.status === 401) { setSession({ authenticated: false }); return; }
    if (!sessionResponse.ok) throw new Error("No se pudo comprobar la sesión.");
    const sessionValue: unknown = await sessionResponse.json();
    const parsedSession = record(sessionValue);
    if (!parsedSession || typeof parsedSession.authenticated !== "boolean") throw new Error("Respuesta de sesión inválida.");
    setSession({ authenticated: parsedSession.authenticated });
    if (!parsedSession.authenticated) return;
    await Promise.all([refreshSnapshot(), refreshQuotas(), refreshHistory()]);
  }, [refreshSnapshot, refreshQuotas, refreshHistory]);

  useEffect(() => {
    if (!snapshot) return;
    const target = window.location.hash.startsWith("#attempt-") ? document.getElementById(decodeURIComponent(window.location.hash.slice(1))) : null;
    target?.scrollIntoView({ block: "center" });
  }, [snapshot === null]);

  useEffect(() => {
    void load().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Error al cargar el panel."));
  }, [load]);

  useEffect(() => {
    if (session?.authenticated !== true) return;
    const timer = window.setInterval(() => {
      void refreshSnapshot().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel."));
      void refreshQuotas().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudieron actualizar las cuotas."));
      void refreshHistory().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el historial."));
    }, 5000);
    return () => window.clearInterval(timer);
  }, [session?.authenticated, refreshSnapshot, refreshQuotas, refreshHistory]);

  useEffect(() => {
    const authenticated = session?.authenticated;
    if (authenticated !== true) return;
    // The gateway stream resumes with Last-Event-ID; the laptop snapshot cursor is a different feed.
    const stream = new EventSource("/api/remote/v1/events");
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
  }, [session?.authenticated, refreshSnapshot]);

  async function sendCommand(event: FormEvent<HTMLFormElement>, command: Record<string, unknown>, key: string) {
    event.preventDefault();
    if (!snapshot) return;
    setWorking(key); setError("");
    const target = record(command.target);
    const origin = `${text(target?.project) ? target.project : ""}/${text(target?.req) ? target.req : ""} · ${text(command.type) ? command.type : "comando"}`;
    const addHistory = (result: string) => setCommandHistory((current) => [{ id: crypto.randomUUID(), at: new Date().toISOString(), origin, result }, ...current].slice(0, 20));
    try {
      const confirmation = record(command.confirmation);
      if (confirmation && text(confirmation.typedReq)) {
        const challengeResponse = await postRemoteMutation("/api/remote/v1/challenges", {
          target: `${text(target?.project) ? target.project : ""}/${text(target?.req) ? target.req : ""}`,
          typedReq: confirmation.typedReq,
        });
        const challengeBody: unknown = await challengeResponse.json().catch(() => null);
        const challenge = record(challengeBody);
        if (!challengeResponse.ok || !text(challenge?.challengeId)) throw new Error(text(record(challengeBody)?.message) ? String(record(challengeBody)?.message) : "No se pudo obtener la confirmación del gateway.");
        command.confirmation = { challengeId: challenge.challengeId, typedReq: confirmation.typedReq };
      }
      const response = await postRemoteMutation("/api/remote/v1/commands", command);
      const responseBody: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const problem = record(responseBody);
        const code = text(problem?.code) ? problem.code : "";
        const message = code === "STALE_PRECONDITION" ? "el estado cambió; actualiza el panel antes de volver a intentarlo." : text(problem?.message) ? problem.message : `El gateway rechazó el comando (${response.status}).`;
        addHistory(`Rechazado · ${message}`);
        throw new Error(message);
      }
      const result = record(responseBody);
      addHistory(text(result?.status) ? result.status : "Aceptado");
      await load();
      setReason("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo enviar el comando."); }
    finally { setWorking(""); }
  }

  function commandForm(type: string, target: Target, state: string, revision: number | undefined, key: string, extra?: Record<string, unknown>) {
    const command = (event: FormEvent<HTMLFormElement>) => {
      const confirmationRequired = ["revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"].includes(type);
      const formData = new FormData(event.currentTarget);
      const confirmationValue = confirmationRequired ? { typedReq: String(formData.get("typedReq") ?? "") } : undefined;
      return sendCommand(event, {
        schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type, target,
        precondition: { state, ...(revision === undefined ? {} : { revision }) },
        ...extra,
        ...(confirmationValue ? { confirmation: confirmationValue } : {}),
      }, key);
    };
    return command;
  }

  function roundForm(round: Round) {
    return (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const form = event.currentTarget;
      const values = new FormData(form);
      const answer: Record<string, unknown> = {};
      for (const question of round.questions) {
        if (question.type === "choice") answer[question.id] = { choice: String(values.get(question.id) ?? ""), note: String(values.get(`${question.id}-note`) ?? "") };
        else answer[question.id] = { text: String(values.get(question.id) ?? "") };
      }
      void sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "answer-round",
        target: { kind: "round", project: round.project, req: round.req, roundId: round.id ?? String(round.round) },
        precondition: { state: round.status, ...(round.revision === undefined ? {} : { revision: round.revision }) },
        round: round.round, answer }, `${round.req}-round-${round.round}`);
    };
  }

  function decisionForm(decision: DecisionRequest, option: DecisionOption) {
    return (event: FormEvent<HTMLFormElement>) => {
      const values = new FormData(event.currentTarget);
      const reason = String(values.get("reason") ?? "").trim();
      if (["retry_with_note", "review_pass", "review_fail"].includes(option.id) && !reason) {
        event.preventDefault(); setError("Esta opción requiere una indicación o razón."); return;
      }
      return sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "answer-decision",
        target: { kind: "run", project: decision.project, req: decision.req, ...(decision.task ? { taskId: decision.task } : {}) },
        precondition: { state: decision.state ?? "waiting", ...(decision.revision === undefined ? {} : { revision: decision.revision }) },
        requestId: decision.id, option: option.id, reason }, `${decision.req}-${decision.id}`);
    };
  }

  function retryForm(run: Run, task: Task) {
    return (event: FormEvent<HTMLFormElement>) => {
      const route = String(new FormData(event.currentTarget).get("route") ?? "");
      void sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "retry",
        target: { kind: "task", project: run.project, req: run.req, taskId: task.id },
        precondition: { state: task.state, ...(task.revision === undefined ? {} : { revision: task.revision }) },
        ...(route ? { route } : {}) }, `${run.req}-${task.id}-retry`);
    };
  }

  function noteForm(run: Run) {
    return (event: FormEvent<HTMLFormElement>) => {
      const note = String(new FormData(event.currentTarget).get("note") ?? "").trim();
      void sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "note",
        target: { kind: "run", project: run.project, req: run.req },
        precondition: { state: run.state, ...(run.revision === undefined ? {} : { revision: run.revision }) }, note }, `${run.req}-note`);
    };
  }

  function editBriefForm(plan: Plan, target: Target) {
    return (event: FormEvent<HTMLFormElement>) => {
      const values = new FormData(event.currentTarget);
      const brief = String(values.get("brief") ?? "").trim();
      const typedReq = String(values.get("typedReq") ?? "");
      void sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "edit-brief", target,
        precondition: { state: plan.state, ...(plan.revision === undefined ? {} : { revision: plan.revision }) }, brief,
        confirmation: { typedReq } }, `${plan.req}-edit-brief`);
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

  const renderTask = (task: Task, run: Run) => <article className="task-card" key={`${run.req}-${task.id}`} id={(task.reviewAttempt ?? task.activeAttempt) ? `attempt-${(task.reviewAttempt ?? task.activeAttempt)!.id}` : undefined}>
    <div className="row-heading"><strong>{task.id}{task.title ? ` · ${task.title}` : ""}</strong><span className="state">{task.state}</span></div>
    <p className="last-seen">Última actividad · {prettyTime(task.activeAttempt?.updatedAt ?? task.updatedAt)}</p>
    {["failed", "rejected"].includes(task.state) && (task.reviewAttempt ?? task.activeAttempt) && <FailureReviewPanel attemptId={(task.reviewAttempt ?? task.activeAttempt)!.id} />}
    {!!task.acceptanceCriteria?.length && <details><summary>Criterios de aceptación ({task.acceptanceCriteria.length})</summary><ul>{task.acceptanceCriteria.map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
    <div className="actions">
      {task.state === "blocked" || task.state === "failed" ? <form onSubmit={commandForm("reopen", { kind: "task", project: run.project, req: run.req, taskId: task.id }, task.state, task.revision, `${run.req}-${task.id}-reopen`)}><button disabled={!!working}>Reabrir</button></form> : null}
      {["blocked", "failed", "rejected"].includes(task.state) && <form className="retry-form" onSubmit={retryForm(run, task)}>
        {availableRoutes.length > 0 && <label>Ruta disponible <select name="route" defaultValue={availableRoutes[0].id} aria-label={`Ruta para reintentar ${task.id}`}>{availableRoutes.map((route) => <option key={route.id} value={route.id}>{route.label}</option>)}</select></label>}
        <button disabled={!!working}>Reintentar</button>
      </form>}
      {task.activeAttempt && <form className="cancel-form" onSubmit={commandForm("cancel-attempt", { kind: "attempt", project: run.project, req: run.req, taskId: task.id, attemptId: task.activeAttempt.id }, task.activeAttempt.state ?? task.state, task.revision, `${run.req}-${task.id}-cancel`, { reason })}><label>Motivo <input required value={reason} onChange={(event) => setReason(event.target.value)} maxLength={2000} /></label><button disabled={!!working || !reason.trim()}>Cancelar intento</button></form>}
    </div>
  </article>;

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
          {["failed", "blocked", "cancelled", "finished"].includes(run.state) ? <form onSubmit={commandForm("reopen", { kind: "run", project: run.project, req: run.req }, run.state, run.revision, `${run.req}-reopen`)}><button disabled={!!working}>Reabrir ejecución</button></form> : null}
          {run.activeAttempt && !run.tasks?.some((task) => task.activeAttempt?.id === run.activeAttempt?.id) && <form className="cancel-form" onSubmit={commandForm("cancel-attempt", { kind: "attempt", project: run.project, req: run.req, attemptId: run.activeAttempt.id }, run.activeAttempt.state ?? run.state, run.revision, `${run.req}-cancel-attempt`, { reason })}><label>Motivo <input required value={reason} onChange={(event) => setReason(event.target.value)} maxLength={2000} /></label><button disabled={!!working || !reason.trim()}>Cancelar intento</button></form>}
          <form className="note-form" onSubmit={noteForm(run)}><label>Dejar una nota <textarea name="note" required maxLength={4000} /></label><button disabled={!!working}>Guardar nota</button></form>
        </div>
        {!!run.tasks?.length && <div className="task-list"><h3>Tareas</h3>{run.tasks.map((task) => renderTask(task, run))}</div>}
        <section className="feed" aria-label={`Feed ${run.req}`}><h3>Actividad reciente</h3>{(() => {
          const rows = typeof window === "undefined" ? [] : window.FlowCore?.groupRows(feed.filter((event) => event.run === `${run.project}/${run.req}`)) ?? [];
          return rows.length ? <ol>{rows.map(({ ev, n, first, last }) => <li key={ev.id}><span className="feed-route">{ev.from} → {ev.to}</span><span>{ev.summary}{n > 1 ? ` ×${n}` : ""}</span><time dateTime={new Date(last * 1000).toISOString()}>{prettyTime(new Date(last * 1000).toISOString())}{first !== last ? ` – ${prettyTime(new Date(first * 1000).toISOString())}` : ""}</time></li>)}</ol> : <p className="empty">Esperando actividad del feed en vivo.</p>;
        })()}</section>
      </article>)}</div>}
    </section>
    {!!snapshot?.plans.length && <section className="runs plans" aria-labelledby="plans-title"><div className="section-heading"><div><p className="eyebrow">REVISIÓN</p><h2 id="plans-title">Planes</h2></div></div><div className="run-list">{snapshot.plans.map((plan) => {
      const target: Target = { kind: "plan", project: plan.project, req: plan.req };
      return <article className="run-card" key={`${plan.project}-${plan.req}-${plan.id ?? "plan"}`}><div className="run-top"><div><p className="eyebrow">{plan.project}</p><h3>{plan.req} · Plan</h3></div><span className="state">{plan.state}</span></div>
        <p className="last-seen">Última actividad · {prettyTime(plan.updatedAt)}</p>
        {[...(plan.acceptanceCriteria ?? []), ...(plan.tasks ?? []).flatMap((task) => task.acceptanceCriteria ?? [])].length > 0 && <details><summary>Criterios de aceptación</summary><ul>{[...(plan.acceptanceCriteria ?? []), ...(plan.tasks ?? []).flatMap((task) => task.acceptanceCriteria ?? [])].map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
        <div className="actions">
          {plan.state === "review" || plan.state === "awaiting-review" ? <form onSubmit={commandForm("approve", target, plan.state, plan.revision, `${plan.req}-approve`)}><label>Escribe {plan.req} para aprobar <input required name="typedReq" pattern={plan.req} autoCapitalize="characters" aria-label={`Escribe ${plan.req} para confirmar la aprobación`} /></label><button disabled={!!working}>Aprobar plan</button></form> : null}
          {plan.state === "approved" ? <form onSubmit={commandForm("launch", target, plan.state, plan.revision, `${plan.req}-launch`)}><label>Escribe {plan.req} para ejecutar <input required name="typedReq" pattern={plan.req} autoCapitalize="characters" aria-label={`Escribe ${plan.req} para confirmar la ejecución`} /></label><button disabled={!!working}>Ejecutar plan</button></form> : null}
          <form onSubmit={commandForm("cancel-plan", target, plan.state, plan.revision, `${plan.req}-cancel-plan`)}><label>Escribe {plan.req} para confirmar <input required name="typedReq" pattern={plan.req} aria-label={`Escribe ${plan.req} para confirmar la cancelación`} /></label><button disabled={!!working}>Cancelar plan</button></form>
          <form onSubmit={commandForm("delete-plan", target, plan.state, plan.revision, `${plan.req}-delete-plan`)}><label>Escribe {plan.req} para confirmar <input required name="typedReq" pattern={plan.req} aria-label={`Escribe ${plan.req} para confirmar la eliminación`} /></label><button className="danger" disabled={!!working}>Eliminar plan</button></form></div>
        {plan.state === "approved" && <form className="edit-brief-form" onSubmit={editBriefForm(plan, target)}><p>La edición creará la revisión {plan.revision === undefined ? "siguiente" : plan.revision + 1}.</p><label>Nuevo brief <textarea name="brief" required minLength={1} maxLength={20000} /></label><label>Escribe {plan.req} para confirmar la edición <input name="typedReq" required pattern={plan.req} aria-label={`Escribe ${plan.req} para confirmar la edición del brief`} /></label><button disabled={!!working}>Editar brief</button></form>}
      </article>;
    })}</div></section>}
    <section className="runs plans quotas" aria-labelledby="quotas-title"><div className="section-heading"><div><p className="eyebrow">CUENTAS</p><h2 id="quotas-title">Cuotas en vivo</h2></div></div>
      {quotas.length ? <div className="run-list">{quotas.map((account) => <article className="run-card quota-card" key={account.id}><div className="run-top"><h3>{account.id}</h3>{account.checkedAt && <span className="last-seen">Actualizado · {prettyTime(account.checkedAt)}</span>}</div>
        {account.windows.length ? <ul className="quota-windows">{account.windows.map((quotaWindow) => <li key={quotaWindow.name}><strong>{quotaWindow.name}</strong><span>{quotaWindow.remaining === undefined ? "Disponible sin dato" : `${quotaWindow.remaining}${quotaWindow.limit === undefined ? " restantes" : ` / ${quotaWindow.limit}`}`}</span>{quotaWindow.resetsAt && <time dateTime={quotaWindow.resetsAt}>Reinicia · {prettyTime(quotaWindow.resetsAt)}</time>}</li>)}</ul> : <p className="empty">Sin ventanas de cuota.</p>}
      </article>)}</div> : <p className="empty">No hay cuotas disponibles.</p>}
    </section>
    {!!snapshot?.rounds?.length && <section className="runs plans" aria-labelledby="rounds-title"><div className="section-heading"><div><p className="eyebrow">PREGUNTAS</p><h2 id="rounds-title">Rondas abiertas</h2></div></div><div className="run-list">{snapshot.rounds.filter((round) => round.status === "open").map((round) => <article className="run-card" key={`${round.project}-${round.req}-${round.round}`}>
      <div className="run-top"><div><p className="eyebrow">{round.project}</p><h3>{round.req} · {round.title || `Ronda ${round.round}`}</h3></div><span className="state">Ronda {round.round}</span></div>
      {round.intro && <p className="last-seen">{round.intro}</p>}{round.coverage && <p className="last-seen">Cobertura · {round.coverage}</p>}
      <form className="answer-form" onSubmit={roundForm(round)}>{round.questions.map((question) => <fieldset className="question" key={question.id}><legend>{question.text}</legend>
        {question.type === "choice" ? <div className="choice-list">{(question.options ?? []).map((option) => <label className="choice-option" key={option.key}><input type="radio" name={question.id} value={option.key} required />
          <span>{option.label}{question.recommended === option.key ? <em> · recomendada</em> : ""}</span></label>)}</div> : <textarea name={question.id} defaultValue={question.suggested ?? ""} required aria-label={question.text} />}
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
    <section className="runs command-history" aria-labelledby="command-history-title"><div className="section-heading"><div><p className="eyebrow">CONTROL</p><h2 id="command-history-title">Historial de comandos</h2></div></div>
      {commandHistory.length ? <ol>{commandHistory.map((item) => <li key={item.id}><span><strong>Origen</strong> · {item.origin}</span><span><strong>Resultado</strong> · {item.result}</span><time dateTime={item.at}>{prettyTime(item.at)}</time></li>)}</ol> : <p className="empty">Todavía no hay comandos registrados.</p>}
    </section>
    <footer className="footer"><span>FLOW REMOTE</span><span>Actualizado · {prettyTime(snapshot?.generatedAt)}</span></footer>
  </main>;
}
