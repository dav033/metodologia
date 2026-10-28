"use client";

import { FormEvent, useEffect, useState } from "react";
import type { QuotaAccount, QuotaWindow, RouteOption } from "../contract.generated";
import { parseQuotas, parseRoutes } from "./remote-contract";

function prettyTime(value?: string | null): string {
  if (!value) return "Sin actividad registrada";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Hora no disponible" : new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export type { RouteOption };

export function RoutesPanel({ project, req, taskId, onRetry, working }: {
  project: string; req: string; taskId: string; working: boolean;
  onRetry: (event: FormEvent<HTMLFormElement>, route: RouteOption) => void;
}) {
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    const query = new URLSearchParams({ target: `${project}/${req}`, task: taskId });
    void fetch(`/api/remote/v1/routes?${query}`, { cache: "no-store" }).then(async (response) => {
      if (!response.ok) throw new Error("No se pudieron cargar las rutas disponibles.");
      const parsed = parseRoutes(await response.json() as unknown);
      if (active) setRoutes(parsed);
    }).catch((cause: unknown) => { if (active) setError(cause instanceof Error ? cause.message : "No se pudieron cargar las rutas disponibles."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [project, req, taskId]);

  return <form className="recovery-form" onSubmit={(event) => {
    event.preventDefault();
    const routeId = String(new FormData(event.currentTarget).get("route") ?? "");
    const route = routes.find((item) => item.routeId === routeId);
    if (route) onRetry(event, route);
  }}>
    <h4>Reintentar tarea</h4>
    {loading ? <p className="empty">Cargando rutas…</p> : error ? <p className="error" role="alert">{error}</p> : routes.length === 0
      ? <p className="empty">No hay rutas disponibles para esta tarea.</p>
      : <>
        <label>Ruta disponible<select name="route" required defaultValue=""><option value="" disabled>Elige una ruta</option>
          {routes.map((route) => <option key={route.routeId} value={route.routeId}>{route.provider} · {route.model} · {route.profile}</option>)}
        </select></label>
        <label>Nota para el próximo intento<textarea name="reason" maxLength={2000} placeholder="Indicación opcional" /></label>
        <button disabled={working}>Reintentar con esta ruta</button>
      </>}
  </form>;
}

export function QuotasPanel() {
  const [accounts, setAccounts] = useState<QuotaAccount[] | null>(null);
  const [checkedAt, setCheckedAt] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const response = await fetch("/api/remote/v1/quotas", { cache: "no-store" });
        if (!response.ok) throw new Error("No se pudieron consultar las cuotas en vivo.");
        const parsed = parseQuotas(await response.json() as unknown);
        if (active) { setAccounts(parsed.accounts); setCheckedAt(parsed.checkedAt); setError(""); }
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "No se pudieron consultar las cuotas en vivo.");
      }
    };
    void refresh();
    const timer = window.setInterval(() => { void refresh(); }, 30_000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);
  const windowLabel = (name: string) => name.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
  const windowValue = (window: QuotaWindow) => `${window.usedPercent}% usado · reinicia ${window.resetsAt ? prettyTime(window.resetsAt) : "reinicio no informado"}`;
  return <section className="runs quotas" aria-labelledby="quotas-title"><div className="section-heading"><div><p className="eyebrow">CUENTAS</p><h2 id="quotas-title">Cuotas en vivo</h2></div><span className="last-seen">{checkedAt ? `Actualizadas · ${prettyTime(checkedAt)}` : "Lectura cada 30 s"}</span></div>
    {error ? <p className="error" role="alert">{error}</p> : accounts === null ? <p className="empty">Consultando cuotas…</p> : accounts.length === 0 ? <p className="empty">No hay cuentas con cuotas disponibles.</p> :
      <div className="quota-list">{accounts.map((account) => <article className="quota-card" key={`${account.provider}-${account.account}`}>
        <div className="row-heading"><strong>{account.account ?? "Cuenta"} · {account.provider ?? "proveedor"}</strong><span className="state">{account.status ?? "desconocido"}</span></div>
        {account.observedAt && <p className="last-seen">Lectura · {prettyTime(account.observedAt)}</p>}
        {account.windows.length ? <ul>{account.windows.map((window) => <li key={window.window}><strong>{windowLabel(window.window)}</strong><span>{windowValue(window)}</span></li>)}</ul> : <p className="last-seen">No hay ventanas de uso registradas.</p>}
      </article>)}</div>}
  </section>;
}
