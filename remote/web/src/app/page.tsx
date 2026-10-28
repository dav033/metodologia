"use client";

/* The "Panel" link leaves this app on purpose: in production `/` is served by the gateway (the local panel). */
/* eslint-disable @next/next/no-html-link-for-pages */

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { QuotasPanel, RoutesPanel } from "./recovery-panels";
import { FailureReviewPanel } from "./failure-review-panel";
import { CHALLENGED_COMMANDS, REOPENABLE_TASK_STATES, STREAM } from "../contract.generated";
import type { CommandHistoryItem, DecisionOption, DecisionRequest, Precondition, RouteOption, SnapshotPlan, SnapshotRound } from "../contract.generated";
import { parseCommandHistory, parseFlowEvent, parseSnapshot, runReopen, type FlowCore, type FlowEvent, type RunView, type SnapshotView, type TaskView } from "./remote-contract";

type Target = { kind: "run" | "attempt" | "task" | "plan" | "round"; project: string; req: string; taskId?: string; attemptId?: string; roundId?: string };
type Session = { authenticated: boolean };
type HistoryRow = { id: string; type: string; target: string; submittedAt: string; origin: string; result: string };
declare global { interface Window { FlowCore?: FlowCore } }

function record(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function text(value: unknown): value is string { return typeof value === "string"; }
const reopenable = (state: string) => (REOPENABLE_TASK_STATES as readonly string[]).includes(state);
const ORIGIN_LABEL: Record<string, string> = { web: "Web", telegram: "Telegram" };
// History rows keep the ledger's result code (CommandHistoryItem.result); people read these labels.
const RESULT_LABEL: Record<string, string> = { OK: "Aplicado", STALE_PRECONDITION: "Rechazado: el estado cambió", REJECTED: "Rechazado",
  FAILED: "Falló", EFFECT_FAILED: "Falló", UNKNOWN_OUTCOME: "Resultado desconocido", ROUTE_UNAVAILABLE: "Rechazado: ruta no disponible" };
const resultLabel = (code: string) => RESULT_LABEL[code] ?? code;

function prettyTime(value?: string | null): string {
  if (!value) return "Sin actividad registrada";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Hora no disponible" : new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export default function HomePage() {
  const [session, setSession] = useState<Session | null>(null);
  const [snapshot, setSnapshot] = useState<SnapshotView | null>(null);
  const [feed, setFeed] = useState<FlowEvent[]>([]);
  const [error, setError] = useState("");
  const [working, setWorking] = useState("");
  const [reason, setReason] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [typedReq, setTypedReq] = useState("");
  const [commandHistory, setCommandHistory] = useState<HistoryRow[]>([]);
  const [historyError, setHistoryError] = useState("");
  const snapshotRequest = useRef(0);
  const reopenedTasks = useRef(new Set<string>());

  const applySnapshot = useCallback((nextSnapshot: SnapshotView) => {
    setSnapshot({ ...nextSnapshot, runs: nextSnapshot.runs.map((run) => ({ ...run, tasks: run.tasks.map((task): TaskView => {
      const key = `${run.project}/${run.req}/${task.id}`;
      if (reopenedTasks.current.has(key) && ["ready", "rejected"].includes(task.state)) {
        return { ...task, reopenedForRecovery: true };
      }
      if (reopenedTasks.current.has(key)) reopenedTasks.current.delete(key);
      return task;
    }) })) });
  }, []);

  const refreshSnapshot = useCallback(async () => {
    const request = ++snapshotRequest.current;
    const response = await fetch("/api/remote/v1/snapshot", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo cargar el estado (${response.status}).`);
    const nextSnapshot = parseSnapshot(await response.json());
    if (request === snapshotRequest.current) applySnapshot(nextSnapshot);
  }, [applySnapshot]);

  const refreshCommandHistory = useCallback(async () => {
    const response = await fetch("/api/remote/v1/commands?after=&limit=100", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo cargar el historial (${response.status}).`);
    const rows = parseCommandHistory(await response.json()).map((item: CommandHistoryItem): HistoryRow => ({
      id: item.id, type: item.command, target: item.target, submittedAt: item.submittedAt, origin: item.origin, result: item.result }));
    setCommandHistory((current) => [...rows, ...current.filter((item) => !rows.some((row) => row.id === item.id))]
      .sort((a, b) => b.submittedAt.localeCompare(a.submittedAt)).slice(0, 100));
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
        await refreshCommandHistory();
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel.");
      } finally {
        if (!stopped) timer = window.setTimeout(() => void poll(), 5000);
      }
    };
    timer = window.setTimeout(() => void poll(), 5000);
    return () => { stopped = true; window.clearTimeout(timer); };
  }, [session?.authenticated, refreshSnapshot, refreshCommandHistory]);

  const snapshotCursor = useRef(snapshot?.cursor);
  snapshotCursor.current = snapshot?.cursor;
  const hasSnapshotCursor = Boolean(snapshot?.cursor);
  useEffect(() => {
    const authenticated = session?.authenticated;
    if (authenticated !== true || !snapshotCursor.current) return;
    // The gateway resumes from the browser's Last-Event-ID (epoch:sequence) and answers a gap with a full `resync`.
    const stream = new EventSource(STREAM.path);
    stream.addEventListener(STREAM.event, (message: MessageEvent<string>) => {
      void refreshSnapshot().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel."));
      try {
        const event = parseFlowEvent(JSON.parse(message.data) as unknown);
        if (event) {
          setFeed((current) => current.some((item) => item.id === event.id) ? current : [...current, event].sort((a, b) => a.ord - b.ord).slice(-500));
          setError("");
        }
      } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo leer el evento remoto."); }
    });
    stream.addEventListener(STREAM.resync, (message: MessageEvent<string>) => {
      try { snapshotRequest.current += 1; applySnapshot(parseSnapshot(JSON.parse(message.data) as unknown)); setError(""); }
      catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo leer el estado remoto."); }
    });
    stream.onerror = () => setError("Se perdió la conexión en vivo; intentando reconectar…");
    return () => stream.close();
  }, [session?.authenticated, hasSnapshotCursor, refreshSnapshot, applySnapshot]);

  async function sendCommand(event: FormEvent<HTMLFormElement>, command: Record<string, unknown>, key: string) {
    event.preventDefault();
    if (!snapshot) return;
    setWorking(key); setError("");
    const target = record(command.target);
    const targetLabel = target && text(target.project) && text(target.req) ? `${target.project}/${target.req}` : "Destino desconocido";
    const commandType = text(command.type) ? command.type : "comando";
    const submittedAt = new Date().toISOString();
    const commandId = text(command.idempotencyKey) ? command.idempotencyKey : `${key}-${submittedAt}`;
    let result = "UNKNOWN_OUTCOME";
    let rejected = false;
    try {
      const mutationHeaders = { "content-type": "application/json", "X-Flow-Request": "1" };
      const confirmation = record(command.confirmation);
      if (confirmation && !text(confirmation.challengeId) && text(confirmation.typedReq)) {
        const challengeResponse = await fetch("/api/remote/v1/challenges", { method: "POST", headers: mutationHeaders,
          body: JSON.stringify({ target: `${text(target?.project) ? target.project : ""}/${text(target?.req) ? target.req : ""}`, typedReq: confirmation.typedReq }) });
        const challengePayload: unknown = await challengeResponse.json().catch(() => null);
        const challenge = record(challengePayload);
        if (!challengeResponse.ok || !text(challenge?.challengeId)) throw new Error(text(challenge?.message) ? challenge.message : "No se pudo obtener la confirmación del gateway.");
        command.confirmation = { challengeId: challenge.challengeId, typedReq: confirmation.typedReq };
      }
      const response = await fetch("/api/remote/v1/commands", { method: "POST", headers: mutationHeaders, body: JSON.stringify(command) });
      const payload: unknown = await response.json().catch(() => null);
      const responseRecord = record(payload);
      if (!response.ok) {
        rejected = true;
        result = text(responseRecord?.code) ? responseRecord.code : "REJECTED";
        if (result === "STALE_PRECONDITION") throw new Error("El estado cambió. Actualiza el panel antes de volver a intentarlo.");
        throw new Error(text(responseRecord?.message) ? responseRecord.message : `El gateway rechazó el comando (${response.status}).`);
      }
      result = text(responseRecord?.code) ? responseRecord.code : text(responseRecord?.status) ? responseRecord.status : "OK";
      if (commandType === "reopen" && target?.kind === "task" && text(target.project) && text(target.req) && text(target.taskId)) {
        reopenedTasks.current.add(`${target.project}/${target.req}/${target.taskId}`);
      }
      if (commandType === "retry" && target?.kind === "task" && text(target.project) && text(target.req) && text(target.taskId)) {
        reopenedTasks.current.delete(`${target.project}/${target.req}/${target.taskId}`);
      }
      await load();
      setCommandHistory((current) => [{ id: commandId, type: commandType, target: targetLabel, submittedAt, origin: "web", result }, ...current.filter((item) => item.id !== commandId)].slice(0, 100));
      setReason(""); setConfirmation(""); setTypedReq("");
    } catch (cause) {
      if (rejected) {
        setCommandHistory((current) => [{ id: commandId, type: commandType, target: targetLabel, submittedAt, origin: "web", result }, ...current.filter((item) => item.id !== commandId)].slice(0, 100));
      }
      setError(cause instanceof Error ? cause.message : "No se pudo enviar el comando.");
    }
    finally { setWorking(""); }
  }

  function commandForm(type: string, target: Target, state: string, revision: number | null | undefined, key: string, extra?: Record<string, unknown>) {
    const command = (event: FormEvent<HTMLFormElement>) => {
      const formValues = new FormData(event.currentTarget);
      const typedReq = formValues.get("typedReq");
      const confirmation = typeof typedReq === "string" && typedReq && (CHALLENGED_COMMANDS as readonly string[]).includes(type)
        ? { confirmation: { ...(record(extra?.confirmation) ?? {}), typedReq } }
        : {};
      const precondition: Precondition = { state, ...(typeof revision === "number" ? { revision } : {}) };
      return sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type, target,
        precondition, ...extra, ...confirmation }, key);
    };
    return command;
  }

  function roundForm(round: SnapshotRound) {
    return (event: FormEvent<HTMLFormElement>) => {
      const values = new FormData(event.currentTarget);
      const answer: Record<string, unknown> = {};
      for (const question of round.questions) {
        if (question.type === "choice") answer[question.id] = { choice: String(values.get(question.id) ?? ""), note: String(values.get(`${question.id}-note`) ?? "") };
        else answer[question.id] = { text: String(values.get(question.id) ?? "") };
      }
      return sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "answer-round",
        target: { kind: "round", project: round.project, req: round.req, roundId: round.id ?? String(round.round) },
        precondition: { state: "open", ...(typeof round.revision === "number" ? { revision: round.revision } : {}) }, round: round.round, answers: answer }, `${round.req}-round-${round.round}`);
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
        precondition: { state: "open" }, requestId: decision.id, option: option.id, reason }, `${decision.req}-${decision.id}`);
    };
  }

  function retryTask(event: FormEvent<HTMLFormElement>, task: TaskView, run: RunView, route: RouteOption) {
    const values = new FormData(event.currentTarget);
    void sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "retry",
      target: { kind: "task", project: run.project, req: run.req, taskId: task.id },
      precondition: { state: task.state },
      route: { routeId: route.routeId, provider: route.provider, model: route.model, account: route.profile },
      reason: String(values.get("reason") ?? "").trim() }, `${run.req}-${task.id}-retry`);
  }

  function editBriefForm(task: TaskView, run: RunView, plan: SnapshotPlan | undefined) {
    return (event: FormEvent<HTMLFormElement>) => {
      const values = new FormData(event.currentTarget);
      const typedReq = String(values.get("typedReq") ?? "");
      void sendCommand(event, { schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type: "edit-brief",
        target: { kind: "task", project: run.project, req: run.req, taskId: task.id },
        precondition: { state: run.state, ...(typeof (plan?.revision ?? run.revision) === "number" ? { revision: plan?.revision ?? run.revision } : {}) },
        field: "objective", value: String(values.get("brief") ?? "").trim(),
        confirmation: { typedReq } }, `${run.req}-${task.id}-edit-brief`);
    };
  }

  if (session === null) {
    return <main className="shell"><header className="topbar"><Link className="brand" href="/remote" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link></header><p className="empty" aria-live="polite">Comprobando sesión…</p></main>;
  }

  if (!session.authenticated) {
    return <main className="shell">
      <header className="topbar"><Link className="brand" href="/remote" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link><span className="environment">PANEL REMOTO</span></header>
      <section className="intro" aria-labelledby="welcome-title"><p className="eyebrow">OPERACIONES · EN VIVO</p><h1 id="welcome-title">Tus ejecuciones,<br /><span>siempre a mano.</span></h1><p className="lede">Inicia sesión para consultar y controlar tus ejecuciones.</p>
        <a className="sign-in" href="/api/auth/github"><svg aria-hidden="true" viewBox="0 0 24 24" width="19" height="19" fill="currentColor"><path d="M12 .9a11.1 11.1 0 0 0-3.51 21.63c.56.1.76-.24.76-.54v-2.08c-3.1.68-3.76-1.32-3.76-1.32-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 .1.85 2.06 3.42 1.45.1-.72.4-1.2.71-1.48-2.47-.28-5.07-1.24-5.07-5.51 0-1.22.44-2.21 1.16-2.99-.12-.28-.5-1.42.11-2.95 0 0 .95-.3 3.06 1.14a10.66 10.66 0 0 1 5.57 0c2.12-1.44 3.06-1.14 3.06-1.14.61 1.53.23 2.67.11 2.95.72.78 1.16 1.77 1.16 2.99 0 4.28-2.6 5.23-5.08 5.5.4.35.76 1.02.76 2.07v3.06c0 .3.2.65.77.54A11.1 11.1 0 0 0 12 .9Z" /></svg>Continuar con GitHub</a>
        <p className="security-note"><span aria-hidden="true">●</span> Acceso privado para el propietario</p>{error && <p className="error" role="alert">{error}</p>}
      </section><footer className="footer"><span>FLOW REMOTE</span><span>CONTROL PLANE · V1</span></footer>
    </main>;
  }

  const renderTask = (task: TaskView, run: RunView) => {
    const plan = snapshot?.plans.find((item) => item.project === run.project && item.req === run.req);
    const nextRevision = (plan?.revision ?? run.revision ?? 0) + 1;
    const canRecover = task.reopenedForRecovery === true;
    const criteria = plan?.tasks.find((item) => item.id === task.id)?.acceptanceCriteria ?? [];
    const reviewAttemptId = task.reviewAttempt?.id ?? [...task.history]
      .reverse().find((attempt) => attempt.state === "failed" || attempt.state === "rejected")?.id ?? undefined;
    return <article className="task-card" key={`${run.req}-${task.id}`}>
    <div className="row-heading"><strong>{task.id}{task.title ? ` · ${task.title}` : ""}</strong><span className="state">{task.state}</span></div>
    <p className="last-seen">Última actividad · {prettyTime(task.activeAttempt?.lastActivityAt ?? task.history.at(-1)?.lastActivityAt ?? undefined)}</p>
    {reopenable(task.state) && reviewAttemptId && <FailureReviewPanel attemptId={reviewAttemptId} target={`${run.project}/${run.req}`} />}
    {!!criteria.length && <details><summary>Criterios de aceptación ({criteria.length})</summary><ul>{criteria.map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
    {canRecover && <RoutesPanel project={run.project} req={run.req} taskId={task.id} working={!!working}
      onRetry={(event, route) => retryTask(event, task, run, route)} />}
    {canRecover && <form className="recovery-form" onSubmit={editBriefForm(task, run, plan)}>
      <h4>Editar brief de {task.id}</h4><p className="last-seen">Creará la revisión {nextRevision}.</p>
      <label>Brief de la tarea<textarea name="brief" required maxLength={4000} defaultValue={task.title ?? ""} /></label>
      <label>Escribe {run.req} para confirmar<input name="typedReq" required autoCapitalize="characters" aria-label={`Escribe ${run.req} para confirmar la edición del brief`} /></label>
      <button disabled={!!working}>Crear revisión y actualizar tarea</button>
    </form>}
    <div className="actions">
      {(reopenable(task.state) || reviewAttemptId) && <Link className="review-back feed-route" href={`/review?project=${encodeURIComponent(run.project)}&req=${encodeURIComponent(run.req)}&taskId=${encodeURIComponent(task.id)}${reviewAttemptId ? `#attempt-${encodeURIComponent(reviewAttemptId)}` : ""}`}>Ver intento fallido</Link>}
      {reopenable(task.state) && !task.reopenedForRecovery ? <form onSubmit={commandForm("reopen", { kind: "task", project: run.project, req: run.req, taskId: task.id }, task.state, undefined, `${run.req}-${task.id}-reopen`)}><button disabled={!!working}>Reabrir</button></form> : null}
      {task.activeAttempt?.id && <form className="cancel-form" onSubmit={commandForm("cancel-attempt", { kind: "attempt", project: run.project, req: run.req, taskId: task.id, attemptId: task.activeAttempt.id ?? "" }, task.activeAttempt.state ?? task.state, undefined, `${run.req}-${task.id}-cancel`, { reason })}><label>Motivo <input required value={reason} onChange={(event) => setReason(event.target.value)} maxLength={2000} /></label><button disabled={!!working || !reason.trim()}>Cancelar intento</button></form>}
    </div>
  </article>;
  };

  return <main className="dashboard shell">
    <header className="topbar"><Link className="brand" href="/remote" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link><div className="header-meta"><span className="environment">{snapshot?.laptop?.online === false ? "LAPTOP SIN CONEXIÓN" : "EN VIVO"}</span><a className="logout" href="/">Panel</a><a className="logout" href="/api/auth/logout">Salir</a></div></header>
    <section className="runs" aria-labelledby="runs-title"><div className="section-heading"><div><p className="eyebrow">CONTROL PLANE · V1</p><h1 id="runs-title">Ejecuciones</h1></div><span className="run-count">{snapshot?.runs.length ?? 0} activas</span></div>
      {error && <p className="error" role="alert">{error}</p>}
      {!snapshot ? <p className="empty">Cargando estado…</p> : snapshot.runs.length === 0 ? <p className="empty">No hay ejecuciones.</p> : <div className="run-list">{snapshot.runs.map((run) => <article className="run-card" key={`${run.project}-${run.req}`}>
        <div className="run-top"><div><p className="eyebrow">{run.project}</p><h2>{run.req}</h2></div><span className="state">{run.state}</span></div>
        <p className="last-seen">Última señal de vida · {prettyTime(run.lastActivityAt ?? run.updatedAt ?? undefined)}</p>
        {(() => {
          const activeTask = run.tasks.find((task) => task.activeAttempt || ["running", "verifying"].includes(task.state));
          const activeAttempt = activeTask?.activeAttempt ?? run.activeAttempt;
          const activeModule = activeAttempt?.state === "verifying" ? "M6" : activeAttempt ? "M3" : run.state === "paused" ? "M1" : "En espera";
          return <div className="activity-strip" aria-label="Actividad actual"><span className="activity-module">{activeModule}</span><span>{activeTask ? `Tarea ${activeTask.id}` : "Sin tarea activa"}</span><span>{activeAttempt ? `Intento ${activeAttempt.id}` : "Sin intento activo"}</span></div>;
        })()}
        <div className="actions">
          {run.state === "running" ? <form onSubmit={commandForm("pause", { kind: "run", project: run.project, req: run.req }, run.state, run.revision, `${run.req}-pause`)}><button disabled={!!working}>Pausar</button></form> : null}
          {run.state === "paused" ? <form onSubmit={commandForm("resume", { kind: "run", project: run.project, req: run.req }, run.state, run.revision, `${run.req}-resume`)}><button disabled={!!working}>Reanudar</button></form> : null}
          {(() => {
            const reopen = runReopen(run);
            return reopen ? <form onSubmit={commandForm("reopen", reopen.target, reopen.precondition.state, undefined, `${run.req}-reopen`)}><button disabled={!!working}>Reabrir ejecución · {reopen.target.taskId}</button></form> : null;
          })()}
          {run.activeAttempt?.id && !run.tasks.some((task) => task.activeAttempt?.id === run.activeAttempt?.id) && <form className="cancel-form" onSubmit={commandForm("cancel-attempt", { kind: "attempt", project: run.project, req: run.req, attemptId: run.activeAttempt.id ?? "" }, run.activeAttempt.state ?? run.state, undefined, `${run.req}-cancel-attempt`, { reason })}><label>Motivo <input required value={reason} onChange={(event) => setReason(event.target.value)} maxLength={2000} /></label><button disabled={!!working || !reason.trim()}>Cancelar intento</button></form>}
        </div>
        {!!run.tasks.length && <div className="task-list"><h3>Tareas</h3>{run.tasks.map((task) => renderTask(task, run))}</div>}
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
        {plan.acceptanceCriteria.length > 0 && <details><summary>Criterios de aceptación</summary><ul>{[...new Set(plan.acceptanceCriteria)].map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
        <div className="actions">
          {plan.state === "review" ? <form onSubmit={commandForm("approve", target, plan.state, plan.revision, `${plan.req}-approve`)}><label>Escribe {plan.req} para aprobar <input required name="typedReq" pattern={plan.req} autoCapitalize="characters" aria-label={`Escribe ${plan.req} para confirmar la aprobación`} /></label><button disabled={!!working}>Aprobar plan</button></form> : null}
          {plan.state === "approved" ? <form onSubmit={commandForm("launch", target, plan.state, plan.revision, `${plan.req}-launch`)}><label>Escribe {plan.req} para ejecutar <input required name="typedReq" pattern={plan.req} autoCapitalize="characters" aria-label={`Escribe ${plan.req} para confirmar la ejecución`} /></label><button disabled={!!working}>Ejecutar plan</button></form> : null}
          <label>Confirmación <input required aria-label="Id del reto de confirmación" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder="Id del reto" /></label><label>Escribe {plan.req} <input required aria-label={`Escribe ${plan.req}`} value={typedReq} onChange={(event) => setTypedReq(event.target.value)} /></label><form onSubmit={commandForm("cancel-plan", target, plan.state, plan.revision, `${plan.req}-cancel-plan`, { confirmation: { challengeId: confirmation, typedReq } })}><button disabled={!!working || !confirmation || typedReq !== plan.req}>Cancelar plan</button></form>
          <form onSubmit={commandForm("delete-plan", target, plan.state, plan.revision, `${plan.req}-delete-plan`, { confirmation: { challengeId: confirmation, typedReq } })}><button className="danger" disabled={!!working || !confirmation || typedReq !== plan.req}>Eliminar plan</button></form></div>
      </article>;
    })}</div></section>}
    {!!snapshot?.rounds.some((round) => round.status === "open") && <section className="runs plans" aria-labelledby="rounds-title"><div className="section-heading"><div><p className="eyebrow">PREGUNTAS</p><h2 id="rounds-title">Rondas abiertas</h2></div></div><div className="run-list">{snapshot.rounds.filter((round) => round.status === "open").map((round) => <article className="run-card" key={`${round.project}-${round.req}-${round.round}`}>
      <div className="run-top"><div><p className="eyebrow">{round.project}</p><h3>{round.req} · {round.title || `Ronda ${round.round}`}</h3></div><span className="state">Ronda {round.round}</span></div>
      {round.intro && <p className="last-seen">{round.intro}</p>}{round.coverage && <p className="last-seen">Cobertura · {round.coverage}</p>}
      <form className="answer-form" onSubmit={roundForm(round)}>{round.questions.map((question) => <fieldset className="question" key={question.id}><legend>{question.text}</legend>
        {question.type === "choice" ? <div className="choice-list">{(question.options ?? []).map((option) => <label className="choice-option" key={option.key}><input type="radio" name={question.id} value={option.key} required /><span>{option.label}{question.recommended === option.key ? <em> · recomendada</em> : ""}</span></label>)}</div> : <textarea name={question.id} defaultValue={question.suggested ?? ""} required aria-label={question.text} />}
        {question.why && <p className="last-seen">{question.why}</p>}{question.type === "choice" && <label className="note-label">Nota opcional <input name={`${question.id}-note`} maxLength={2000} /></label>}
      </fieldset>)}<button disabled={!!working}>Enviar respuestas</button></form>
    </article>)}</div></section>}
    {!!snapshot?.decisionRequests.length && <section className="runs plans" aria-labelledby="decisions-title"><div className="section-heading"><div><p className="eyebrow">DECISIONES</p><h2 id="decisions-title">Esperando tu decisión</h2></div></div><div className="run-list">{snapshot.decisionRequests.map((decision) => <article className="run-card" key={decision.id}>
      <div className="run-top"><div><p className="eyebrow">{decision.project} · {decision.req}{decision.task ? ` · ${decision.task}` : ""}</p><h3>{decision.title}</h3></div>{decision.unskippable && <span className="state">Requiere revisión</span>}</div>
      <p className="last-seen">{decision.what}</p>{!!decision.evidence.length && <details><summary>Evidencia</summary><ul>{decision.evidence.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul></details>}
      <div className="decision-options">{decision.options.map((option) => <form className={`decision-option${decision.recommended === option.id ? " recommended" : ""}`} key={option.id} onSubmit={decisionForm(decision, option)}>
        <h4>{option.label}{decision.recommended === option.id ? <span> · recomendada</span> : ""}</h4><p>{option.consequence}</p>
        {["retry_with_note", "review_pass", "review_fail"].includes(option.id) && <label className="note-label">Indicación o razón <textarea name="reason" required maxLength={2000} /></label>}
        <button disabled={!!working}>Elegir esta opción</button>
      </form>)}</div>
    </article>)}</div></section>}
    <section className="runs history" aria-labelledby="command-history-title"><div className="section-heading"><div><p className="eyebrow">TRAZABILIDAD</p><h2 id="command-history-title">Historial de comandos</h2></div></div>{historyError && <p className="error" role="status">{historyError}</p>}{commandHistory.length ? <ol className="command-history">{commandHistory.map((item) => <li key={item.id}><strong>{item.type}</strong><span>{item.target}</span><time dateTime={item.submittedAt}>{prettyTime(item.submittedAt)}</time><span>Origen · {ORIGIN_LABEL[item.origin] ?? item.origin}</span><span>Resultado · {resultLabel(item.result)}</span></li>)}</ol> : <p className="empty">Aún no se han enviado comandos desde este panel.</p>}</section>
    <footer className="footer"><span>FLOW REMOTE</span><span>Actualizado · {prettyTime(snapshot?.generatedAt)}</span></footer>
  </main>;
}
