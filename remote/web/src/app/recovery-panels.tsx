"use client";

import { FormEvent, useEffect, useState } from "react";

export type RouteOption = { routeId: string; provider: string; model: string; profile: string; available: boolean };
type QuotaAccount = { profile: string; provider: string; status: string; observedAt?: number; windows: Record<string, unknown> };

function record(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}
function text(value: unknown): value is string { return typeof value === "string"; }
function field(source: Record<string, unknown>, camel: string, snake: string): unknown { return source[camel] ?? source[snake]; }
function prettyTime(value?: string): string {
  if (!value) return "Sin actividad registrada";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Hora no disponible" : new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

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
      const body = record(await response.json() as unknown);
      if (!response.ok || !body || !Array.isArray(body.routes)) throw new Error("No se pudieron cargar las rutas disponibles.");
      const parsed = body.routes.flatMap((value): RouteOption[] => {
        const route = record(value);
        const routeId = route && field(route, "routeId", "route_id");
        const profile = route && field(route, "profile", "account");
        return route && text(routeId) && text(route.provider) && text(route.model) && text(profile) && typeof route.available === "boolean"
          ? [{ routeId, provider: route.provider, model: route.model, profile, available: route.available }]
          : [];
      }).filter((route) => route.available);
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
        const body = record(await response.json() as unknown);
        if (!response.ok || !body || !Array.isArray(body.accounts)) throw new Error("No se pudieron consultar las cuotas en vivo.");
        const parsed = body.accounts.flatMap((value): QuotaAccount[] => {
          const account = record(value);
          const profile = account && field(account, "profile", "account");
          const observedAt = field(account ?? {}, "observedAt", "observed_at");
          const windows = record(account?.windows);
          return account && text(profile) && text(account.provider) && text(account.status) && windows
            ? [{ profile, provider: account.provider, status: account.status,
                observedAt: typeof observedAt === "number" ? observedAt : undefined, windows }]
            : [];
        });
        if (active) { setAccounts(parsed); setCheckedAt(text(body.checkedAt) ? body.checkedAt : ""); setError(""); }
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "No se pudieron consultar las cuotas en vivo.");
      }
    };
    void refresh();
    const timer = window.setInterval(() => { void refresh(); }, 30_000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);
  const windowLabel = (name: string) => name.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
  const windowValue = (value: unknown) => {
    const item = record(value);
    if (!item) return "Dato no disponible";
    const used = typeof item.used_percent === "number" ? `${item.used_percent}% usado` : "Uso desconocido";
    const reset = typeof item.resets_at === "number" ? prettyTime(new Date(item.resets_at * 1000).toISOString()) : "reinicio no informado";
    return `${used} · reinicia ${reset}`;
  };
  return <section className="runs quotas" aria-labelledby="quotas-title"><div className="section-heading"><div><p className="eyebrow">CUENTAS</p><h2 id="quotas-title">Cuotas en vivo</h2></div><span className="last-seen">{checkedAt ? `Actualizadas · ${prettyTime(checkedAt)}` : "Lectura cada 30 s"}</span></div>
    {error ? <p className="error" role="alert">{error}</p> : accounts === null ? <p className="empty">Consultando cuotas…</p> : accounts.length === 0 ? <p className="empty">No hay cuentas con cuotas disponibles.</p> :
      <div className="quota-list">{accounts.map((account) => <article className="quota-card" key={`${account.provider}-${account.profile}`}>
        <div className="row-heading"><strong>{account.profile} · {account.provider}</strong><span className="state">{account.status}</span></div>
        {account.observedAt && <p className="last-seen">Lectura · {prettyTime(new Date(account.observedAt * 1000).toISOString())}</p>}
        {Object.keys(account.windows).length ? <ul>{Object.entries(account.windows).map(([name, value]) => <li key={name}><strong>{windowLabel(name)}</strong><span>{windowValue(value)}</span></li>)}</ul> : <p className="last-seen">No hay ventanas de uso registradas.</p>}
      </article>)}</div>}
  </section>;
}
