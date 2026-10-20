"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { PlansPanel } from "./plans-panel";
import { field, parseSnapshot, record, text, type Run, type Snapshot, type Task } from "../lib/snapshot";

type Target = { kind: "run" | "attempt" | "task" | "plan" | "round"; project: string; req: string; taskId?: string; attemptId?: string };
type Session = { authenticated: boolean };
type FlowEvent = { id: string; cursor: string; run: string; seq: string; ord: number; task: string; attempt: string; from: string; to: string; kind: string; summary: string; at_epoch: number };
type CommandRecord = { id: string; command: string; target: string; submittedAt: string; origin: string; result: string };
type FailureReview = { attemptId: string; cause: string; verification: { command: string | null; output: string; checks: { command: string; exitCode: number | null; output: string }[] }; diff: { stat: string | null; files: string[] }; logTail: string };
type FlowCore = { groupRows(events: FlowEvent[]): { ev: FlowEvent; n: number; first: number; last: number }[]; taskState(state: string): string };
declare global { interface Window { FlowCore?: FlowCore } }

function parseFlowEvent(value: unknown): FlowEvent | null {
  const event = record(value);
  const target = record(event?.target);
  const data = record(event?.data);
  if (!event || event.schemaVersion !== 1 || !target || !data || !text(event.id) || !text(event.cursor) || !text(event.type) || !text(target.project) || !text(target.req) || !text(event.occurredAt)) return null;
  const project = target.project;
  const req = target.req;
  if (!project || !req) return null;
  const task = text(field(target, "taskId", "task")) ? String(field(target, "taskId", "task")) : "";
  const attempt = text(field(target, "attemptId", "attempt")) ? String(field(target, "attemptId", "attempt")) : "";
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
  return { id: event.id, cursor: event.cursor, run: `${project}/${req}`, seq: event.cursor, ord: date.valueOf(), task,
    attempt, from, to, kind, summary: text(data.summary) ? data.summary : text(data.message) ? data.message : event.type,
    at_epoch: date.valueOf() / 1000 };
}

function prettyTime(value?: string): string {
  if (!value) return "Sin actividad registrada";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Hora no disponible" : new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function redactSecrets(value: string): string {
  return value.replace(/\b(FLOW_GATEWAY_KEY|TELEGRAM_BOT_TOKEN|GITHUB_CLIENT_SECRET)\s*(?:=|:)\s*(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;]+)/gi, "$1=[REDACTED]");
}

function parseFailureReview(value: unknown): FailureReview {
  const review = record(value);
  const verification = record(review?.verification);
  const diff = record(review?.diff);
  if (!review || !text(review.attemptId) || !text(review.cause) || !verification || !diff || !text(review.logTail)) {
    throw new Error("La respuesta del gateway no cumple el contrato de revisión v1.");
  }
  const checks = Array.isArray(verification.checks) ? verification.checks.flatMap((item) => {
    const check = record(item);
    if (!check || !text(check.command) || !text(check.output)) return [];
    return [{ command: redactSecrets(check.command), exitCode: typeof check.exitCode === "number" ? check.exitCode : null, output: redactSecrets(check.output) }];
  }) : [];
  return {
    attemptId: review.attemptId, cause: redactSecrets(review.cause),
    verification: { command: text(verification.command) ? redactSecrets(verification.command) : null,
      output: text(verification.output) ? redactSecrets(verification.output) : "", checks },
    diff: { stat: text(diff.stat) ? redactSecrets(diff.stat) : null,
      files: Array.isArray(diff.files) ? diff.files.filter(text).map(redactSecrets) : [] },
    logTail: redactSecrets(review.logTail),
  };
}

export default function HomePage() {
  const [session, setSession] = useState<Session | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [feed, setFeed] = useState<FlowEvent[]>([]);
  const [reviews, setReviews] = useState<Record<string, FailureReview>>({});
  const [reviewErrors, setReviewErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [working, setWorking] = useState("");
  const [reason, setReason] = useState("");
    const [commands, setCommands] = useState<CommandRecord[]>([]);
  const [historyError, setHistoryError] = useState("");

  const load = useCallback(async () => {
    const sessionResponse = await fetch("/api/auth/session", { cache: "no-store" });
    if (sessionResponse.status === 401) { setSession({ authenticated: false }); return; }
    if (!sessionResponse.ok) throw new Error("No se pudo comprobar la sesión.");
    const parsedSession = record(await sessionResponse.json() as unknown);
    if (!parsedSession || !text(parsedSession.login)) throw new Error("Respuesta de sesión inválida.");
    setSession({ authenticated: true });
    const response = await fetch("/api/remote/v1/snapshot", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo cargar el estado (${response.status}).`);
    setSnapshot(parseSnapshot(await response.json()));
    const historyResponse = await fetch("/api/remote/v1/commands?after=&limit=100", { cache: "no-store" });
    if (historyResponse.ok) {
      const history: unknown = await historyResponse.json();
      const historyRecord = record(history);
      if (historyRecord && Array.isArray(historyRecord.commands)) {
        setHistoryError("");
        setCommands(historyRecord.commands.flatMap((item): CommandRecord[] => {
        const row = record(item);
        if (!row || !text(row.command) || !text(row.target) || !text(row.origin)) return [];
        const id = field(row, "id", "idempotency_key");
        const submittedAt = field(row, "submittedAt", "received_at");
        const result = field(row, "result", "status");
        return text(id) && text(submittedAt) && text(result) ? [{ id, command: row.command, target: row.target, submittedAt, origin: row.origin, result }] : [];
        }));
      } else setHistoryError("La respuesta del historial de comandos no es válida.");
    } else setHistoryError(`El historial de comandos no está disponible (${historyResponse.status}).`);
  }, []);

  useEffect(() => {
    void load().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Error al cargar el panel."));
  }, [load]);

  useEffect(() => {
    if (session?.authenticated !== true) return;
    const source = new EventSource("/api/remote/v1/events");
    source.addEventListener("flow", (message) => {
      try {
        const event = parseFlowEvent(JSON.parse((message as MessageEvent<string>).data) as unknown);
        if (!event) throw new Error("Evento remoto inválido.");
        setFeed((current) => [...current, event].filter((item, index, all) => all.findIndex((candidate) => candidate.id === item.id) === index).sort((a, b) => a.ord - b.ord).slice(-500));
        if (event.kind === "state_change") void load().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel."));
      } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo leer la actividad remota."); }
    });
    source.addEventListener("reset", () => { source.close(); void load().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar el panel.")); });
    source.onerror = () => setError("No se pudo leer la actividad remota.");
    return () => source.close();
  }, [session?.authenticated, load]);

  async function sendCommand(command: Record<string, unknown>, key: string): Promise<boolean> {
    if (!snapshot) return false;
    setWorking(key); setError("");
    try {
      let payload = command;
      const commandType = command.type;
      if (["revise", "approve", "launch", "cancel-plan", "delete-plan"].includes(String(commandType))) {
        const confirmationValue = record(command.confirmation);
        const target = record(command.target);
        if (!confirmationValue || !text(confirmationValue.typedReq) || !target || confirmationValue.typedReq !== target.req) throw new Error("Escribe el id de requerimiento para confirmar.");
        const challengeResponse = await fetch("/api/remote/v1/challenges", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ target, typedReq: confirmationValue.typedReq }) });
        const challenge: unknown = await challengeResponse.json();
        const challengeRecord = record(challenge);
        if (!challengeResponse.ok || !challengeRecord || !text(challengeRecord.challengeId)) throw new Error(text(challengeRecord?.message) ? challengeRecord.message : "No se pudo confirmar el requerimiento.");
        payload = { ...command, confirmation: { challengeId: challengeRecord.challengeId, typedReq: confirmationValue.typedReq } };
      }
      const response = await fetch("/api/remote/v1/commands", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
      const result: unknown = await response.json();
      const resultRecord = record(result);
      if (!response.ok) {
        if (resultRecord?.code === "STALE_PRECONDITION") throw new Error("El estado cambió. Actualiza el panel antes de volver a intentarlo.");
        throw new Error(text(resultRecord?.message) ? resultRecord.message : `El gateway rechazó el comando (${response.status}).`);
      }
      await load();
      setReason("");
      return true;
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo enviar el comando."); return false; }
    finally { setWorking(""); }
  }

  async function loadFailureReview(attemptId: string) {
    setReviewErrors((current) => ({ ...current, [attemptId]: "" }));
    try {
      const response = await fetch(`/api/remote/v1/attempts/${encodeURIComponent(attemptId)}/review`, { cache: "no-store" });
      if (!response.ok) throw new Error(`No se pudo cargar la revisión (${response.status}).`);
      const review = parseFailureReview(await response.json());
      setReviews((current) => ({ ...current, [attemptId]: review }));
    } catch (cause) {
      setReviewErrors((current) => ({ ...current, [attemptId]: cause instanceof Error ? cause.message : "No se pudo cargar la revisión." }));
    }
  }

  function commandForm(type: string, target: Target, state: string, revision: number | undefined, key: string, extra?: Record<string, unknown>) {
    const params: Record<string, unknown> = { ...(extra ?? {}) };
    if (type === "cancel-attempt") params.attempt = target.attemptId;
    if (type === "reopen") params.task = target.taskId;
    const command = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); return void sendCommand({
      schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type, target,
      precondition: { state, ...(revision === undefined ? {} : { revision }) },
      ...(text(params.reason) ? { reason: params.reason } : {}),
      ...(type === "cancel-attempt" ? { reason: params.reason } : {}),
    }, key); };
    return command;
  }

  if (session === null) {
    return <main className="shell"><header className="topbar"><Link className="brand" href="/" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link></header><p className="empty" aria-live="polite">Comprobando sesión…</p></main>;
  }

  if (!session.authenticated) {
    return <main className="shell">
      <header className="topbar"><Link className="brand" href="/" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link><span className="environment">PANEL REMOTO</span></header>
      <section className="intro" aria-labelledby="welcome-title"><p className="eyebrow">OPERACIONES · EN VIVO</p><h1 id="welcome-title">Tus ejecuciones,<br /><span>siempre a mano.</span></h1><p className="lede">Inicia sesión para consultar y controlar tus ejecuciones.</p>
        <a className="sign-in" href="/api/auth/login"><svg aria-hidden="true" viewBox="0 0 24 24" width="19" height="19" fill="currentColor"><path d="M12 .9a11.1 11.1 0 0 0-3.51 21.63c.56.1.76-.24.76-.54v-2.08c-3.1.68-3.76-1.32-3.76-1.32-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 .1.85 2.06 3.42 1.45.1-.72.4-1.2.71-1.48-2.47-.28-5.07-1.24-5.07-5.51 0-1.22.44-2.21 1.16-2.99-.12-.28-.5-1.42.11-2.95 0 0 .95-.3 3.06 1.14a10.66 10.66 0 0 1 5.57 0c2.12-1.44 3.06-1.14 3.06-1.14.61 1.53.23 2.67.11 2.95.72.78 1.16 1.77 1.16 2.99 0 4.28-2.6 5.23-5.08 5.5.4.35.76 1.02.76 2.07v3.06c0 .3.2.65.77.54A11.1 11.1 0 0 0 12 .9Z" /></svg>Continuar con GitHub</a>
        <p className="security-note"><span aria-hidden="true">●</span> Acceso privado para el propietario</p>{error && <p className="error" role="alert">{error}</p>}
      </section><footer className="footer"><span>FLOW REMOTE</span><span>CONTROL PLANE · V1</span></footer>
    </main>;
  }

  const renderTask = (task: Task, run: Run) => <article className="task-card" key={`${run.req}-${task.id}`}>
    <div className="row-heading"><strong>{task.id}{task.title ? ` · ${task.title}` : ""}</strong><span className="state">{task.state}</span></div>
    <p className="last-seen">Última actividad · {prettyTime(task.activeAttempt?.updatedAt ?? task.updatedAt)}</p>
    {!!task.acceptanceCriteria?.length && <details><summary>Criterios de aceptación ({task.acceptanceCriteria.length})</summary><ul>{task.acceptanceCriteria.map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
    <div className="actions">
      {task.state === "blocked" || task.state === "failed" ? <form onSubmit={commandForm("reopen", { kind: "task", project: run.project, req: run.req, taskId: task.id }, task.state, task.revision, `${run.req}-${task.id}-reopen`)}><button disabled={!!working}>Reabrir</button></form> : null}
      {task.activeAttempt && <form className="cancel-form" onSubmit={commandForm("cancel-attempt", { kind: "attempt", project: run.project, req: run.req, taskId: task.id, attemptId: task.activeAttempt.id }, task.activeAttempt.state ?? task.state, task.revision, `${run.req}-${task.id}-cancel`, { reason })}><label>Motivo <input required value={reason} onChange={(event) => setReason(event.target.value)} maxLength={2000} /></label><button disabled={!!working || !reason.trim()}>Cancelar intento</button></form>}
    </div>
    {task.history?.filter((attempt) => ["failed", "rejected"].includes(attempt.state ?? "") || attempt.failure).map((attempt) => <section className="failure-review" key={attempt.id} aria-label={`Revisión del intento ${attempt.id}`}>
      <button className="review-trigger" onClick={() => void loadFailureReview(attempt.id)}>Revisar intento fallido · {attempt.id}</button>
      {reviewErrors[attempt.id] && <p className="error" role="alert">{reviewErrors[attempt.id]}</p>}
      {reviews[attempt.id] && <div className="review-sections">
        <section><h4>Causa</h4><p>{reviews[attempt.id].cause}</p></section>
        <section><h4>Verificación</h4><p>{reviews[attempt.id].verification.command ?? "Sin comando registrado"}</p>
          {reviews[attempt.id].verification.checks.map((check, index) => <p key={`${check.command}-${index}`}>{check.command} · salida {check.exitCode ?? "desconocida"}</p>)}
          <pre className="review-log" aria-label="Salida de verificación">{reviews[attempt.id].verification.output || "Sin salida registrada"}</pre></section>
        <section><h4>Diff</h4><p>{reviews[attempt.id].diff.stat ?? "Sin estadísticas de cambios"}</p>
          {reviews[attempt.id].diff.files.length > 0 && <ul>{reviews[attempt.id].diff.files.map((file) => <li key={file}>{file}</li>)}</ul>}</section>
        <section><h4>Registro del agente</h4><pre className="review-log" aria-label="Registro del agente">{reviews[attempt.id].logTail || "Sin líneas de registro"}</pre></section>
      </div>}
    </section>)}
  </article>;

  return <main className="dashboard shell">
    <header className="topbar"><Link className="brand" href="/" aria-label="Flow Remote, inicio"><span className="brand-mark">F</span><span>flow<span className="brand-muted">/remote</span></span></Link><div className="header-meta"><span className="environment">{snapshot?.laptopStatus === "offline" ? "LAPTOP SIN CONEXIÓN" : "EN VIVO"}</span></div></header>
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
        </div>
        {!!run.tasks?.length && <div className="task-list"><h3>Tareas</h3>{run.tasks.map((task) => renderTask(task, run))}</div>}
        <section className="feed" aria-label={`Feed ${run.req}`}><h3>Actividad reciente</h3>{(() => {
          const rows = typeof window === "undefined" ? [] : window.FlowCore?.groupRows(feed.filter((event) => event.run === `${run.project}/${run.req}`)) ?? [];
          return rows.length ? <ol>{rows.map(({ ev, n, first, last }) => <li key={ev.id}><span className="feed-route">{ev.from} → {ev.to}</span><span>{ev.summary}{n > 1 ? ` ×${n}` : ""}</span><time dateTime={new Date(last * 1000).toISOString()}>{prettyTime(new Date(last * 1000).toISOString())}{first !== last ? ` – ${prettyTime(new Date(first * 1000).toISOString())}` : ""}</time></li>)}</ol> : <p className="empty">Esperando actividad del feed en vivo.</p>;
        })()}</section>
      </article>)}</div>}
    </section>
    {snapshot && <PlansPanel plans={snapshot.plans} working={working} send={sendCommand} prettyTime={prettyTime} />}
    <section className="runs history" aria-labelledby="history-title"><div className="section-heading"><div><p className="eyebrow">TRAZABILIDAD</p><h2 id="history-title">Historial de comandos</h2></div></div>{historyError ? <p className="error" role="status">{historyError}</p> : commands.length ? <ol className="command-history">{commands.map((command) => <li key={command.id}><strong>{command.command}</strong><span>{command.target}</span><time>{prettyTime(command.submittedAt)}</time><span>Origen · {command.origin}</span><span>Resultado · {command.result}</span></li>)}</ol> : <p className="empty">No hay comandos registrados.</p>}</section>
    <footer className="footer"><span>FLOW REMOTE</span><span>Actualizado · {prettyTime(snapshot?.generatedAt)}</span></footer>
  </main>;
}
