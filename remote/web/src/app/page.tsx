"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

type Run = {
  project: string;
  req: string;
  state: string;
  activity?: string;
  lastSignOfLife?: string;
};

type View =
  | { kind: "loading" }
  | { kind: "login" }
  | { kind: "runs"; runs: Run[]; laptopOnline: boolean | null }
  | { kind: "error"; message: string };

type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? value as JsonRecord
    : null;
}

function firstText(record: JsonRecord, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return undefined;
}

function parseRuns(value: unknown): { runs: Run[]; laptopOnline: boolean | null } {
  const snapshot = asRecord(value);
  if (!snapshot || snapshot.schemaVersion !== 1 || !Array.isArray(snapshot.runs)) {
    throw new Error("El gateway devolvió un snapshot inválido.");
  }

  const runs = snapshot.runs.map((value): Run => {
    const run = asRecord(value);
    if (!run) throw new Error("El gateway devolvió una ejecución inválida.");

    const project = firstText(run, "project");
    const req = firstText(run, "req", "req_id");
    const state = firstText(run, "state", "status");
    if (!project || !req || !state) throw new Error("El gateway devolvió una ejecución incompleta.");

    const activeAttempt = asRecord(run.activeAttempt) ?? asRecord(run.attempt);
    return {
      project,
      req,
      state,
      activity: firstText(run, "agent_now", "agentNow", "active_task_title")
        ?? firstText(asRecord(run.active_task) ?? {}, "title", "id"),
      lastSignOfLife: firstText(run, "last_sign_of_life", "lastSeenAt", "last_seen_at", "last_seen", "updatedAt", "updated_at")
        ?? firstText(activeAttempt ?? {}, "last_activity_at", "updatedAt", "updated_at"),
    };
  });

  const laptop = asRecord(snapshot.laptop);
  return {
    runs,
    laptopOnline: typeof laptop?.online === "boolean" ? laptop.online : null,
  };
}

function prettyTime(value?: string): string {
  if (!value) return "Sin señal registrada";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "Hora no disponible";
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Bogota",
  }).format(date);
}

function stateLabel(state: string): string {
  const labels: Record<string, string> = {
    running: "En curso",
    paused: "En pausa",
    blocked: "Bloqueada",
    failed: "Fallida",
    completed: "Completada",
    finished: "Completada",
    pending: "Pendiente",
    awaiting_review: "Requiere revisión",
    "awaiting-review": "Requiere revisión",
  };
  return labels[state] ?? state.replaceAll("_", " ");
}

function Header({ online }: { online?: boolean | null }) {
  return (
    <header className="topbar">
      <Link className="brand" href="/" aria-label="Flow Remote, inicio">
        <span className="brand-mark" aria-hidden="true">F</span>
        <span>flow<span className="brand-muted">/remote</span></span>
      </Link>
      <span className="environment">
        {online === false ? "EQUIPO SIN CONEXIÓN" : "PANEL REMOTO"}
      </span>
    </header>
  );
}

function LoginScreen() {
  return (
    <main className="shell">
      <Header />
      <section className="intro" aria-labelledby="welcome-title">
        <p className="eyebrow">OPERACIONES · EN VIVO</p>
        <h1 id="welcome-title">Tus ejecuciones,<br /><span>siempre a mano.</span></h1>
        <p className="lede">Inicia sesión para consultar el estado de tus ejecuciones desde cualquier lugar.</p>
        <a className="sign-in" href="/api/auth/github">
          <svg aria-hidden="true" viewBox="0 0 24 24" width="19" height="19" fill="currentColor">
            <path d="M12 .9a11.1 11.1 0 0 0-3.51 21.63c.56.1.76-.24.76-.54v-2.08c-3.1.68-3.76-1.32-3.76-1.32-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 .1.85 2.06 3.42 1.45.1-.72.4-1.2.71-1.48-2.47-.28-5.07-1.24-5.07-5.51 0-1.22.44-2.21 1.16-2.99-.12-.28-.5-1.42.11-2.95 0 0 .95-.3 3.06 1.14a10.66 10.66 0 0 1 5.57 0c2.12-1.44 3.06-1.14 3.06-1.14.61 1.53.23 2.67.11 2.95.72.78 1.16 1.77 1.16 2.99 0 4.28-2.6 5.23-5.08 5.5.4.35.76 1.02.76 2.07v3.06c0 .3.2.65.77.54A11.1 11.1 0 0 0 12 .9Z" />
          </svg>
          Continuar con GitHub
        </a>
        <p className="security-note"><span aria-hidden="true">●</span> Acceso privado para dav033</p>
      </section>
      <footer className="footer"><span>FLOW REMOTE</span><span>CONTROL PLANE · V1</span></footer>
    </main>
  );
}

function RunsScreen({ runs, laptopOnline }: { runs: Run[]; laptopOnline: boolean | null }) {
  return (
    <main className="dashboard shell">
      <Header online={laptopOnline} />
      <section className="runs" aria-labelledby="runs-title">
        <div className="section-heading">
          <div><p className="eyebrow">CONTROL PLANE · V1</p><h1 id="runs-title">Ejecuciones</h1></div>
          <span className="run-count">{runs.length} {runs.length === 1 ? "ejecución" : "ejecuciones"}</span>
        </div>
        {runs.length === 0 ? (
          <p className="empty">No hay ejecuciones para mostrar.</p>
        ) : (
          <div className="run-list" aria-label="Lista de ejecuciones">
            {runs.map((run) => (
              <article className="run-card" key={`${run.project}/${run.req}`}>
                <div className="run-top">
                  <div className="run-identity"><p className="eyebrow">{run.project}</p><h2>{run.req}</h2></div>
                  <span className={`run-status status-${run.state}`}><span className="status-dot" aria-hidden="true" />{stateLabel(run.state)}</span>
                </div>
                <p className="run-activity">{run.activity ?? "Sin actividad reportada"}</p>
                <dl className="run-meta"><div><dt>Última señal de vida</dt><dd>{prettyTime(run.lastSignOfLife)}</dd></div></dl>
              </article>
            ))}
          </div>
        )}
      </section>
      <footer className="footer"><span>FLOW REMOTE</span><span>Estado actualizado automáticamente</span></footer>
    </main>
  );
}

export default function HomePage() {
  const [view, setView] = useState<View>({ kind: "loading" });

  const load = useCallback(async () => {
    const sessionResponse = await fetch("/api/auth/session", { cache: "no-store", credentials: "same-origin" });
    if (sessionResponse.status === 401) {
      setView({ kind: "login" });
      return;
    }
    if (!sessionResponse.ok) throw new Error("No se pudo comprobar la sesión.");

    const sessionValue: unknown = await sessionResponse.json();
    const session = asRecord(sessionValue);
    const authenticated = typeof session?.login === "string" && session.login.length > 0
      || session?.authenticated === true;
    if (!authenticated) {
      setView({ kind: "login" });
      return;
    }

    const snapshotResponse = await fetch("/api/remote/v1/snapshot", { cache: "no-store", credentials: "same-origin" });
    if (!snapshotResponse.ok) throw new Error(`No se pudo cargar el estado (${snapshotResponse.status}).`);
    const snapshotValue: unknown = await snapshotResponse.json();
    setView({ kind: "runs", ...parseRuns(snapshotValue) });
  }, []);

  useEffect(() => {
    let active = true;
    const refresh = () => load().catch((cause: unknown) => {
      if (active) setView({ kind: "error", message: cause instanceof Error ? cause.message : "Error al cargar el panel." });
    });
    void refresh();
    const timer = window.setInterval(() => { void refresh(); }, 5_000);
    return () => { active = false; window.clearInterval(timer); };
  }, [load]);

  if (view.kind === "login") return <LoginScreen />;
  if (view.kind === "runs") return <RunsScreen runs={view.runs} laptopOnline={view.laptopOnline} />;
  if (view.kind === "error") {
    return <main className="shell"><Header /><p className="error" role="alert">{view.message}</p></main>;
  }
  return <main className="shell"><Header /><p className="empty" aria-live="polite">Comprobando sesión…</p></main>;
}
