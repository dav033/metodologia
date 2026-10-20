"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";

type Target = { kind: "run" | "attempt" | "task" | "plan" | "round"; project: string; req: string; taskId?: string; attemptId?: string };
type Run = { project: string; req: string; state: string; updatedAt?: string; lastSeenAt?: string; revision?: number; activeAttempt?: { id: string; state?: string; updatedAt?: string }; tasks?: Task[] };
type Task = { id: string; title?: string; state: string; revision?: number; updatedAt?: string; acceptanceCriteria?: string[]; activeAttempt?: { id: string; state?: string; updatedAt?: string } };
type Plan = { id?: string; project: string; req: string; state: string; revision?: number; updatedAt?: string; acceptanceCriteria?: string[]; tasks?: Task[] };
type Snapshot = { schemaVersion: 1; generatedAt: string; cursor: string; runs: Run[]; plans: Plan[]; laptop?: { online: boolean; checkedAt?: string } };
type Session = { authenticated: boolean };
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
    return { id: task.id, title: text(task.title) ? task.title : undefined, state: task.state,
      revision: typeof task.revision === "number" ? task.revision : undefined,
      updatedAt: text(updatedAt) ? updatedAt : undefined,
      acceptanceCriteria: Array.isArray(criteria) ? criteria.filter(text) : [],
      activeAttempt: parseAttempt(field(task, "activeAttempt", "active_attempt")) };
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
  const laptop = record(raw.laptop);
  const cursor = raw.cursor;
  return { schemaVersion: 1, generatedAt: String(generatedAt), cursor: String(cursor), runs, plans,
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
  const snapshotRequest = useRef(0);

  const refreshSnapshot = useCallback(async () => {
    const request = ++snapshotRequest.current;
    const response = await fetch("/api/remote/v1/snapshot", { cache: "no-store" });
    if (!response.ok) throw new Error(`No se pudo cargar el estado (${response.status}).`);
    const nextSnapshot = parseSnapshot(await response.json());
    if (request === snapshotRequest.current) setSnapshot(nextSnapshot);
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
    await refreshSnapshot();
  }, [refreshSnapshot]);

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
  }, [session?.authenticated, refreshSnapshot]);

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
    try {
      const response = await fetch("/api/remote/v1/commands", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(command) });
      if (!response.ok) throw new Error(`El gateway rechazó el comando (${response.status}).`);
      await load();
      setReason(""); setConfirmation(""); setTypedReq("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo enviar el comando."); }
    finally { setWorking(""); }
  }

  function commandForm(type: string, target: Target, state: string, revision: number | undefined, key: string, extra?: Record<string, unknown>) {
    const command = (event: FormEvent<HTMLFormElement>) => sendCommand(event, {
      schemaVersion: 1, idempotencyKey: `web-${crypto.randomUUID()}`, type, target,
      precondition: { state, ...(revision === undefined ? {} : { revision }) }, ...extra,
    }, key);
    return command;
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

  const renderTask = (task: Task, run: Run) => <article className="task-card" key={`${run.req}-${task.id}`}>
    <div className="row-heading"><strong>{task.id}{task.title ? ` · ${task.title}` : ""}</strong><span className="state">{task.state}</span></div>
    <p className="last-seen">Última actividad · {prettyTime(task.activeAttempt?.updatedAt ?? task.updatedAt)}</p>
    {!!task.acceptanceCriteria?.length && <details><summary>Criterios de aceptación ({task.acceptanceCriteria.length})</summary><ul>{task.acceptanceCriteria.map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></details>}
    <div className="actions">
      {(task.state === "failed" || task.activeAttempt?.state === "failed") && <Link className="review-back" href="/review">Ver intento fallido</Link>}
      {task.state === "blocked" || task.state === "failed" ? <form onSubmit={commandForm("reopen", { kind: "task", project: run.project, req: run.req, taskId: task.id }, task.state, task.revision, `${run.req}-${task.id}-reopen`)}><button disabled={!!working}>Reabrir</button></form> : null}
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
        <div className="actions"><form onSubmit={commandForm("cancel-plan", target, plan.state, plan.revision, `${plan.req}-cancel-plan`, { confirmation: { challengeId: confirmation, typedReq } })}><label>Confirmación <input required aria-label="Id del reto de confirmación" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder="Id del reto" /></label><label>Escribe {plan.req} <input required value={typedReq} onChange={(event) => setTypedReq(event.target.value)} /></label><button disabled={!!working}>Cancelar plan</button></form>
          <form onSubmit={commandForm("delete-plan", target, plan.state, plan.revision, `${plan.req}-delete-plan`, { confirmation: { challengeId: confirmation, typedReq } })}><button className="danger" disabled={!!working}>Eliminar plan</button></form></div>
      </article>;
    })}</div></section>}
    <footer className="footer"><span>FLOW REMOTE</span><span>Actualizado · {prettyTime(snapshot?.generatedAt)}</span></footer>
  </main>;
}
