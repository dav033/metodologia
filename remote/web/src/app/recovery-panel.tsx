"use client";

import { useState } from "react";
import { editBriefCommand, noteCommand, retryCommand, type Command } from "../lib/commands";
import { parseRoutes, type Plan, type QuotaAccount, type Run, type RouteOption, type Task } from "../lib/snapshot";

type Send = (command: Command, key: string) => Promise<boolean>;
const uuid = () => crypto.randomUUID();
const routeLabel = (route: RouteOption) => `${route.provider}/${route.model}${route.account ? ` · ${route.account}` : ""}${route.available ? "" : " · no disponible"}`;

/** Retry with an optionally pinned route, leave a note, or edit the brief of one task. */
export function TaskRecovery({ run, task, plan, working, send }: { run: Run; task: Task; plan?: Plan; working: string; send: Send }) {
  const [routes, setRoutes] = useState<RouteOption[] | null>(null);
  const [routeError, setRouteError] = useState("");
  const [route, setRoute] = useState("");
  const [instruction, setInstruction] = useState("");
  const [note, setNote] = useState("");
  const [brief, setBrief] = useState(task.objective ?? "");
  const [criteria, setCriteria] = useState((task.acceptanceCriteria ?? []).join("\n"));
  const key = `${run.req}-${task.id}`;
  const nextRevision = plan?.planRevision === undefined ? undefined : plan.planRevision + 1;
  const criteriaList = criteria.split("\n").map((line) => line.trim()).filter(Boolean);

  async function loadRoutes() {
    setRouteError("");
    try {
      const query = new URLSearchParams({ target: `${run.project}/${run.req}`, task: task.id });
      const response = await fetch(`/api/remote/v1/routes?${query.toString()}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`No se pudieron cargar las rutas (${response.status}).`);
      const parsed = parseRoutes(await response.json());
      setRoutes(parsed);
      setRoute("");
    } catch (cause) { setRouteError(cause instanceof Error ? cause.message : "No se pudieron cargar las rutas."); }
  }

  return <details className="recovery" aria-label={`Recuperación ${task.id}`}><summary>Recuperar {task.id}</summary>
    <section aria-label={`Reintento ${task.id}`}>
      <h4>Reintentar</h4>
      <button type="button" onClick={() => void loadRoutes()}>Ver rutas disponibles</button>
      {routeError && <p className="error" role="alert">{routeError}</p>}
      {routes && <label>Ruta fijada <select aria-label={`Ruta para ${task.id}`} value={route} onChange={(event) => setRoute(event.target.value)}>
        <option value="">Sin fijar (elige el sistema)</option>
        {routes.map((option) => <option key={option.id} value={option.id} disabled={!option.available}>{routeLabel(option)}</option>)}</select></label>}
      <label>Indicación para el agente <textarea aria-label={`Indicación para ${task.id}`} maxLength={2000} value={instruction} onChange={(event) => setInstruction(event.target.value)} /></label>
      <button disabled={!!working} onClick={() => void send(retryCommand(run, task.id, route || undefined, instruction, uuid()), `${key}-retry`)}>{route ? "Reintentar con la ruta fijada" : "Reintentar"}</button>
    </section>
    <section aria-label={`Nota ${task.id}`}>
      <h4>Dejar una nota</h4>
      <textarea aria-label={`Nota para ${task.id}`} maxLength={4000} value={note} onChange={(event) => setNote(event.target.value)} />
      <button disabled={!!working || !note.trim()} onClick={() => void send(noteCommand(run, task.id, note, uuid()), `${key}-note`).then((ok) => { if (ok) setNote(""); })}>Guardar nota</button>
    </section>
    {plan && <form aria-label={`Brief ${task.id}`} onSubmit={(event) => { event.preventDefault(); void send(editBriefCommand(plan, task.id, brief, criteriaList, uuid()), `${key}-brief`); }}>
      <h4>Editar brief</h4>
      <label>Objetivo <textarea aria-label={`Objetivo de ${task.id}`} maxLength={20000} value={brief} onChange={(event) => setBrief(event.target.value)} /></label>
      <label>Criterios de aceptación (uno por línea) <textarea aria-label={`Criterios de ${task.id}`} value={criteria} onChange={(event) => setCriteria(event.target.value)} /></label>
      <p className="last-seen">{nextRevision === undefined ? "Creará una nueva revisión del plan." : `Creará la revisión r${nextRevision} del plan (hoy r${plan.planRevision}).`}</p>
      <button disabled={!!working || !brief.trim() || plan.planRevision === undefined}>Guardar brief</button>
    </form>}
  </details>;
}

const percent = (value: number) => `${Math.round(value)} %`;
const windowName = (name: string) => name === "five_hour" ? "5 horas" : name === "seven_day" ? "7 días" : name;

export function QuotasPanel({ accounts, error, prettyTime }: { accounts: QuotaAccount[]; error: string; prettyTime: (value?: string) => string }) {
  return <section className="runs quotas" aria-labelledby="quotas-title"><div className="section-heading"><div><p className="eyebrow">SUSCRIPCIONES</p><h2 id="quotas-title">Cuotas</h2></div></div>
    {error ? <p className="error" role="status">{error}</p> : accounts.length === 0 ? <p className="empty">Sin datos de cuota.</p> : <ul className="quota-list">{accounts.map((account) => <li key={account.account} aria-label={`Cuota ${account.account}`}>
      <strong>{account.account}</strong> <span className="state">{account.provider}</span>{account.status !== "ok" && <span className="state">{account.status}</span>}
      <ul>{account.windows.length ? account.windows.map((window) => <li key={window.window}><span>{windowName(window.window)}</span> <progress max={100} value={window.usedPercent} aria-label={`${account.account} ${windowName(window.window)}`} /> <span>{percent(window.usedPercent)} usado</span>{window.resetsAt && <span> · renueva {prettyTime(window.resetsAt)}</span>}</li>) : <li className="empty">Sin ventanas medidas.</li>}</ul></li>)}</ul>}
  </section>;
}
