# Solucionador 20261030-085358-d06c — pictures REQ-021 (run pictures:REQ-021:r26)

Started 2026-10-30T08:53:58 by the durable engine's maintenance pass.

## Triggers

- `pictures:REQ-021:r26:resolution:33917a4fe713f9d06f614144e4061848` — resolution · CG-9: the conflict in src/app/admin/gasto/page.tsx waits for a recorded resolution since 2026-10-30T08:51:42; no retry can settle it
- `pictures:REQ-021:r26:resolution:95e324edf1c0f6a2dfa846402a03e8fd` — resolution · CG-9: the conflict in src/components/admin/GastoIa.tsx waits for a recorded resolution since 2026-10-30T08:51:42; no retry can settle it
- `pictures:REQ-021:r26:resolution:ae405794f9e8c98682e388a7740da9f6` — resolution · CG-9: the conflict in src/lib/ia/nucleo/python-adapter.ts waits for a recorded resolution since 2026-10-30T08:51:42; no retry can settle it

## Resolution request 33917a4fe713f9d06f614144e4061848 (src/app/admin/gasto/page.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/33917a4fe713f9d06f614144e4061848.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/33917a4fe713f9d06f614144e4061848.diff3`
- blobs: base `-`, ours `5727c71fa02fff8bfdf1c8c5958840f74a0bf749`, theirs `605541d53a00f832c1e64303a7364e01b4e60e1a` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "7042b3ba371b48ba11ce556009d7b489c478b25e", "ours": "7514afd0c0904f5e33ccccfb9746e9b322215e2c", "theirs": "217e5e5053d0497c4867ff21dae3c33e3fd8170a"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/33917a4fe713f9d06f614144e4061848.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (src/app/admin/gasto/page.tsx)
import Link from "next/link";
import { cookies } from "next/headers";
import { GastoIa } from "@/components/admin/GastoIa";
import { SESSION_COOKIE } from "@/lib/auth/session";
import { PERMISOS } from "@/lib/cuentas/permisos";
import { resolverSesion } from "@/lib/cuentas/sesion";

export const instant = false;

export default async function GastoIaPage() {
  let session = null;
  try {
    const token = (await cookies()).get(SESSION_COOKIE)?.value;
    if (token && /^[A-Za-z0-9_-]{43}$/.test(token)) session = await resolverSesion(token);
  } catch {
    return <AccessState title="No se pudo comprobar el acceso" message="Inténtalo de nuevo más tarde." />;
  }

  if (!session) return <AccessState title="Inicia sesión para continuar" message="El gasto de IA requiere una sesión y permiso de acceso." action="Iniciar sesión" href="/login" />;
  if (!session.permissions.includes(PERMISOS.gasto_ia)) return <AccessState title="Sin acceso" message="Tu cuenta no tiene permiso para ver el gasto de IA." action="Abrir Mi cuenta" href="/cuenta" />;
  return <GastoIa canManageAccounts={session.permissions.includes(PERMISOS.administracion_usuarios)} canManageRoles={session.permissions.includes(PERMISOS.administracion_roles)} />;
}

function AccessState({ title, message, action, href }: { title: string; message: string; action?: string; href?: string }) {
  return <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-8 sm:px-7 lg:px-10" lang="es">
    <header className="mb-6 flex items-center justify-between gap-4"><h1 className="text-2xl font-semibold text-texto">Gasto de IA</h1><Link href="/" className="ui-button-ghost min-h-11 rounded-full px-4">← Volver a herramientas</Link></header>
    <section className="mx-auto max-w-xl rounded-[2rem] border border-borde bg-superficie p-8 text-center"><h2 className="text-xl font-semibold text-texto">{title}</h2><p className="my-4 text-texto-suave">{message}</p>{action && href ? <Link className="ui-button-primary inline-flex min-h-11 items-center rounded-full px-5" href={href}>{action}</Link> : null}</section>
  </main>;
}
||||||| base
=======
import Link from "next/link";
import { cookies } from "next/headers";
import { GastoIa } from "@/components/admin/GastoIa";
import { SESSION_COOKIE } from "@/lib/auth/session";
import { PERMISOS } from "@/lib/cuentas/permisos";
import { resolverSesion } from "@/lib/cuentas/sesion";

export const instant = false;

export default async function GastoIaPage() {
  let session = null;
  try {
    const token = (await cookies()).get(SESSION_COOKIE)?.value;
    if (token && /^[A-Za-z0-9_-]{43}$/.test(token)) session = await resolverSesion(token);
  } catch {
    return <AccessState title="No se pudo comprobar el acceso" message="Inténtalo de nuevo más tarde." />;
  }

  if (!session) return <AccessState title="Inicia sesión para continuar" message="El gasto de IA requiere una sesión y permiso de acceso." action="Iniciar sesión" href="/login" />;
  if (!session.permissions.includes(PERMISOS.gasto_ia)) return <AccessState title="Sin acceso" message="Tu cuenta no tiene permiso para ver el gasto de IA." action="Abrir Mi cuenta" href="/cuenta" />;
  return <GastoIa canManageAccounts={session.permissions.includes(PERMISOS.administracion_usuarios)} canManageRoles={session.permissions.includes(PERMISOS.administracion_roles)} />;
}

function AccessState({ title, message, action, href }: { title: string; message: string; action?: string; href?: string }) {
  return <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-8 sm:px-7 lg:px-10" lang="es">
    <header className="mb-6 flex items-center justify-between gap-4"><h1 className="text-2xl font-semibold text-texto">Gasto de IA</h1><Link href="/" className="ui-button-ghost min-h-11 rounded-full px-4">← Volver al chat</Link></header>
    <section className="mx-auto max-w-xl rounded-[2rem] border border-borde bg-superficie p-8 text-center"><h2 className="text-xl font-semibold text-texto">{title}</h2><p className="my-4 text-texto-suave">{message}</p>{action && href ? <Link className="ui-button-primary inline-flex min-h-11 items-center rounded-full px-5" href={href}>{action}</Link> : null}</section>
  </main>;
}
>>>>>>> theirs

```

## Resolution request 95e324edf1c0f6a2dfa846402a03e8fd (src/components/admin/GastoIa.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/95e324edf1c0f6a2dfa846402a03e8fd.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/95e324edf1c0f6a2dfa846402a03e8fd.diff3`
- blobs: base `-`, ours `9856947de225967b82fb683e650c75bec615d674`, theirs `3866455db8f69e49fa93f97ccf6b38cffbdd4280` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "7042b3ba371b48ba11ce556009d7b489c478b25e", "ours": "7514afd0c0904f5e33ccccfb9746e9b322215e2c", "theirs": "217e5e5053d0497c4867ff21dae3c33e3fd8170a"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/95e324edf1c0f6a2dfa846402a03e8fd.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (src/components/admin/GastoIa.tsx)
"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

type Call = {
  kind: string; tool: string | null; provider: string | null; model: string | null;
  inputTokens: string | null; outputTokens: string | null; thoughtTokens: string | null; cacheTokens: string | null;
  costUsd: string | null; currency: string; status: string; occurredAt: string;
  session: string; conversation: string; workItem: string; accountName: string;
};
type Group = {
  key: string; title: string; accountName: string; session: string; workItem: string;
  count: number; costUsd: string | null; callsWithCost: number; calls: Call[];
};
type PageData = {
  summary: { calls: number; accounts: number; sessions: number; costUsd: string | null; callsWithCost: number; inputTokens: string | null; outputTokens: string | null; partialCalls: number; errorCalls: number };
  users: { id: string; name: string }[]; tools: string[]; groups: Group[]; nextCursor: string | null;
};

function money(amount: string | null): string {
  if (amount === null) return "Desconocido";
  const [whole = "0", fraction = ""] = amount.split(".");
  let decimals = (fraction + "0000").slice(0, 4);
  let integer = whole;
  if ((fraction[4] ?? "0") >= "5") {
    const rounded = addIntegerStrings(decimals, "1");
    if (rounded.length > 4) { integer = addIntegerStrings(integer, "1"); decimals = "0000"; }
    else decimals = rounded.padStart(4, "0");
  }
  return `${groupThousands(integer)}.${decimals}`;
}
const number = (amount: string | null) => amount === null ? "No informado" : groupThousands(amount);
const groupThousands = (amount: string) => amount.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
function addIntegerStrings(left: string, right: string): string {
  let carry = 0;
  let result = "";
  let leftIndex = left.length - 1;
  let rightIndex = right.length - 1;
  while (leftIndex >= 0 || rightIndex >= 0 || carry) {
    const sum = Number(left[leftIndex--] ?? "0") + Number(right[rightIndex--] ?? "0") + carry;
    result = String(sum % 10) + result;
    carry = Math.floor(sum / 10);
  }
  return result.replace(/^0+(?=\d)/, "");
}

export function GastoIa({ canManageAccounts, canManageRoles }: { canManageAccounts: boolean; canManageRoles: boolean }) {
  const [user, setUser] = useState("");
  const [kind, setKind] = useState("");
  const [tool, setTool] = useState("");
  const [groupBy, setGroupBy] = useState<"session" | "work" | "user">("session");
  const [data, setData] = useState<PageData | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<"user" | "kind" | "tool" | null>(null);
  const [error, setError] = useState(false);
  const [openGroup, setOpenGroup] = useState<string | null>(null);

  const query = useMemo(() => {
    const params = new URLSearchParams({ groupBy });
    if (user) params.set("user", user);
    if (kind) params.set("kind", kind);
    if (tool) params.set("tool", tool);
    return params;
  }, [user, kind, tool, groupBy]);

  const load = useCallback(async (next: string | null, append: boolean) => {
    setLoading(true);
    setError(false);
    if (!append) { setData(null); setGroups([]); setOpenGroup(null); }
    try {
      const params = new URLSearchParams(query);
      if (next) params.set("cursor", next);
      const response = await fetch(`/api/admin/gasto?${params}`, { cache: "no-store" });
      if (!response.ok) throw new Error("gasto fetch failed");
      const result = await response.json() as PageData;
      setData(result);
      setGroups((current) => append ? [...current, ...result.groups] : result.groups);
      setCursor(result.nextCursor);
      if (!append) setOpenGroup(result.groups[0]?.key ?? null);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
      setActiveFilter(null);
    }
  }, [query]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(null, false); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  function clearFilters() {
    setUser(""); setKind(""); setTool("");
  }

  return (
    <main className="mx-auto w-full min-w-0 max-w-7xl flex-1 px-5 py-8 sm:px-7 lg:px-10" lang="es">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-texto">Gasto de IA</h1>
        <Link href="/" className="ui-button-ghost min-h-11 rounded-full px-4">← Volver a herramientas</Link>
      </header>
      <nav aria-label="Administración" className="mb-5 flex flex-wrap gap-2 border-b border-borde pb-3 text-sm">
        {canManageAccounts ? <Link href="/admin/cuentas" className="rounded-full px-4 py-2 text-texto-suave hover:bg-superficie-2">Cuentas</Link> : null}
        {canManageRoles ? <Link href="/admin/roles" className="rounded-full px-4 py-2 text-texto-suave hover:bg-superficie-2">Roles y permisos</Link> : null}
        <span aria-current="page" className="rounded-full bg-superficie-2 px-4 py-2 font-medium text-texto">Gasto de IA</span>
      </nav>

      <section aria-label="Revisión de gasto" aria-busy={loading} className="rounded-[2rem] border border-borde bg-superficie p-5 shadow-sm sm:p-7">
        <p className="mb-5 text-sm text-texto-suave">Fecha de las llamadas · UTC · Solo metadatos de uso</p>
        <div aria-label="Filtros" className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1fr_auto] xl:items-end">
          <label className="grid gap-2 text-sm font-medium text-texto">Usuario
            <select value={user} onChange={(event) => { setActiveFilter("user"); setUser(event.target.value); }} disabled={loading && activeFilter !== "user"} className="min-h-11 rounded-full border border-borde bg-background px-4 text-texto focus-visible:outline focus-visible:outline-3 focus-visible:outline-acento">
              <option value="">Todos</option>{data?.users.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <fieldset className="grid gap-2 text-sm font-medium text-texto"><legend>Tipo de llamada</legend>
            <div className="grid grid-cols-3 gap-1 rounded-full bg-superficie-2 p-1">
              {[["", "Todos"], ["text", "Texto"], ["image", "Imagen"]].map(([value, label]) => <button key={value} type="button" aria-pressed={kind === value} onClick={() => { setActiveFilter("kind"); setKind(value!); }} disabled={loading && activeFilter !== "kind"} className="min-h-11 rounded-full px-3 text-sm aria-pressed:bg-superficie aria-pressed:text-texto text-texto-suave">{label}</button>)}
            </div>
          </fieldset>
          <details className="group">
            <summary className="flex min-h-11 cursor-pointer list-none items-center rounded-full px-4 text-sm font-medium text-texto focus-visible:outline focus-visible:outline-3 focus-visible:outline-acento">Herramienta: {tool || "Todas"}⌄</summary>
            <label className="mt-2 grid gap-2 text-sm text-texto-suave">Herramienta
              <select value={tool} onChange={(event) => { setActiveFilter("tool"); setTool(event.target.value); }} disabled={loading && activeFilter !== "tool"} className="min-h-11 rounded-full border border-borde bg-background px-4 text-texto">
                <option value="">Todas</option>{data?.tools.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
          </details>
          <button type="button" onClick={clearFilters} disabled={loading || (!user && !kind && !tool)} className="ui-button-ghost min-h-11 rounded-full px-4 disabled:opacity-50">Limpiar filtros</button>
        </div>

        {error ? <div role="alert" className="rounded-3xl bg-error-suave p-6 text-texto"><h2 className="text-xl font-semibold">No se pudo cargar el gasto</h2><p className="my-3">No se muestran totales sin confirmar. Conservamos los filtros para que puedas reintentar.</p><button className="ui-button-primary min-h-11 rounded-full px-5" onClick={() => void load(null, false)}>Reintentar</button></div> : null}
        {!error && loading && !data ? <div role="status" className="space-y-3"><p>Cargando gasto…</p>{[0, 1, 2].map((item) => <div key={item} className="h-20 animate-pulse rounded-3xl bg-superficie-2" />)}</div> : null}
        {!error && !loading && data?.summary.calls === 0 ? <div role="status" className="py-10 text-center"><h2 className="text-xl font-semibold">No hay llamadas para estos filtros</h2><p className="my-3 text-texto-suave">Cambia o limpia los filtros para revisar otras llamadas.</p><button onClick={clearFilters} className="ui-button-primary min-h-11 rounded-full px-5">Limpiar filtros</button></div> : null}
        {!error && data && data.summary.calls > 0 ? <>
          <div aria-live="polite" aria-atomic="true" className="mb-7 grid gap-5 rounded-3xl border border-borde p-5 sm:grid-cols-[1.2fr_1fr] sm:p-6">
            <div><p className="text-sm text-texto-suave">Coste estimado conocido · USD</p><p className="font-mono text-3xl font-semibold tabular-nums text-texto">${money(data.summary.costUsd)}</p><p className="text-sm text-texto-suave">{data.summary.callsWithCost} / {data.summary.calls} llamadas con coste informado</p></div>
            <div className="text-sm text-texto-suave"><p>{data.summary.calls} llamadas · {data.summary.accounts} cuentas · {data.summary.sessions} sesiones</p><p className="mt-2">Tokens de entrada: {number(data.summary.inputTokens)} · de salida: {number(data.summary.outputTokens)} · totales conocidos: No informado</p><p className="mt-2">Total de todos los resultados filtrados; importes estimados, no factura.</p></div>
          </div>
          {data.summary.partialCalls + data.summary.errorCalls > 0 ? <p role="status" className="mb-5 rounded-3xl bg-aviso-suave p-4 text-sm text-aviso">Hay errores del proveedor con uso facturable conocido y metadatos incompletos. El coste conocido se incluye. Lo no informado queda desconocido; no equivale a cero.</p> : null}
          <nav aria-label="Agrupar gasto" className="mb-5 grid gap-2 sm:flex">
            {([["session", "Por sesión"], ["work", "Por proyecto o conversación"], ["user", "Por usuario"]] as const).map(([value, label]) => <button key={value} aria-pressed={groupBy === value} onClick={() => setGroupBy(value)} className="min-h-11 rounded-full px-4 text-left text-sm text-texto-suave aria-pressed:bg-superficie-2 aria-pressed:text-texto">{label}</button>)}
          </nav>
          <div className="space-y-3">
            {groups.map((group) => <section key={group.key} className="overflow-hidden rounded-3xl border border-borde">
              <h2><button type="button" aria-expanded={openGroup === group.key} onClick={() => setOpenGroup(openGroup === group.key ? null : group.key)} className="grid min-h-20 w-full grid-cols-[1fr_auto] items-center gap-3 p-5 text-left focus-visible:outline focus-visible:outline-3 focus-visible:outline-acento sm:grid-cols-[1fr_1fr_auto]">
                <span><span className="block text-lg font-semibold text-texto">{group.title}</span><span className="block text-sm text-texto-suave">{group.accountName} · {group.count} llamadas · {group.workItem}</span></span>
                <span className="text-sm text-texto-suave">Sesión …{group.session}</span><span className="font-mono text-texto">{group.costUsd === null ? "Desconocido" : `$${money(group.costUsd)}`}</span>
              </button></h2>
              {openGroup === group.key ? <div className="space-y-3 bg-superficie-suave p-4 sm:p-5">
                <p className="text-sm text-texto-suave">{group.callsWithCost} / {group.count} llamadas con coste informado</p>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <div><span className="font-medium text-texto">Por tipo · </span>{Object.entries(group.calls.reduce<Record<string, string[]>>((totals, call) => { if (call.costUsd !== null) (totals[call.kind] ??= []).push(call.costUsd); return totals; }, {})).map(([name, amounts]) => <span key={name} className="mr-3 text-texto-suave">{name}: ${money(sumAmounts(amounts))}</span>)}</div>
                  <div><span className="font-medium text-texto">Por herramienta · </span>{Object.entries(group.calls.reduce<Record<string, string[]>>((totals, call) => { if (call.costUsd !== null) (totals[call.tool ?? "No informada"] ??= []).push(call.costUsd); return totals; }, {})).map(([name, amounts]) => <span key={name} className="mr-3 text-texto-suave">{name}: ${money(sumAmounts(amounts))}</span>)}</div>
                </div>
                {group.calls.map((call, index) => <details key={`${group.key}-${call.occurredAt}-${index}`} className="rounded-2xl border border-borde bg-superficie p-4">
                  <summary className="flex min-h-11 cursor-pointer flex-wrap items-center justify-between gap-2 font-medium text-texto">{call.kind} · {call.tool ?? "Herramienta no informada"}<span>{call.costUsd === null ? "Desconocido" : `$${money(call.costUsd)}`}</span></summary>
                  <dl className="mt-3 grid gap-x-5 gap-y-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
                    {[["Usuario", call.accountName], ["Sesión", `…${call.session}`], ["Proyecto / conversación", `${call.workItem} / …${call.conversation}`], ["Proveedor / modelo", `${call.provider ?? "No informado"} / ${call.model ?? "No informado"}`], ["Tokens de entrada", number(call.inputTokens)], ["Tokens de salida", number(call.outputTokens)], ["Tokens totales informados", "No informado"], ["Fecha · UTC", call.occurredAt], ["Estado", call.status === "completed" ? "Completada" : call.status === "partial" ? "Error del proveedor · uso parcial facturable" : "Error del proveedor · coste desconocido"]].map(([label, value]) => <div key={label}><dt className="text-xs text-texto-suave">{label}</dt><dd className="break-words text-texto">{value}</dd></div>)}
                  </dl>
                </details>)}
              </div> : null}
            </section>)}
          </div>
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 text-sm text-texto-suave"><p>{groups.length} grupos mostrados · Los totales incluyen todos los resultados.</p>{cursor ? <button disabled={loading} onClick={() => void load(cursor, true)} className="ui-button-primary min-h-11 rounded-full px-5">Cargar más</button> : null}</div>
          <p className="mt-6 rounded-2xl bg-superficie-2 p-4 text-sm text-texto-suave">Solo metadatos de uso. Sin prompts, respuestas ni contenido generado.</p>
        </> : null}
      </section>
      <footer className="py-6 text-center text-xs text-texto-suave">Pictures · Sempertex</footer>
    </main>
  );
}

function sumAmounts(amounts: string[]): string | null {
  if (!amounts.length) return null;
  let whole = "0";
  let fraction = 0;
  for (const amount of amounts) {
    const [itemWhole = "0", itemFraction = ""] = amount.split(".");
    whole = addIntegerStrings(whole, itemWhole);
    fraction += Number((itemFraction + "0000000000").slice(0, 10));
    if (fraction >= 10_000_000_000) { whole = addIntegerStrings(whole, "1"); fraction -= 10_000_000_000; }
  }
  return `${whole}.${String(fraction).padStart(10, "0")}`;
}
||||||| base
=======
"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

type Call = {
  kind: string; tool: string | null; provider: string | null; model: string | null;
  inputTokens: string | null; outputTokens: string | null; thoughtTokens: string | null; cacheTokens: string | null;
  costUsd: string | null; currency: string; status: string; occurredAt: string;
  session: string; conversation: string; workItem: string; accountName: string;
};
type Group = {
  key: string; title: string; accountName: string; session: string; workItem: string;
  count: number; costUsd: string | null; callsWithCost: number; calls: Call[];
};
type PageData = {
  summary: { calls: number; accounts: number; sessions: number; costUsd: string | null; callsWithCost: number; inputTokens: string | null; outputTokens: string | null; partialCalls: number; errorCalls: number };
  users: { id: string; name: string }[]; tools: string[]; groups: Group[]; nextCursor: string | null;
};

function money(amount: string | null): string {
  if (amount === null) return "Desconocido";
  const [whole = "0", fraction = ""] = amount.split(".");
  let decimals = (fraction + "0000").slice(0, 4);
  let integer = whole;
  if ((fraction[4] ?? "0") >= "5") {
    const rounded = addIntegerStrings(decimals, "1");
    if (rounded.length > 4) { integer = addIntegerStrings(integer, "1"); decimals = "0000"; }
    else decimals = rounded.padStart(4, "0");
  }
  return `${groupThousands(integer)}.${decimals}`;
}
const number = (amount: string | null) => amount === null ? "No informado" : groupThousands(amount);
const groupThousands = (amount: string) => amount.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
function addIntegerStrings(left: string, right: string): string {
  let carry = 0;
  let result = "";
  let leftIndex = left.length - 1;
  let rightIndex = right.length - 1;
  while (leftIndex >= 0 || rightIndex >= 0 || carry) {
    const sum = Number(left[leftIndex--] ?? "0") + Number(right[rightIndex--] ?? "0") + carry;
    result = String(sum % 10) + result;
    carry = Math.floor(sum / 10);
  }
  return result.replace(/^0+(?=\d)/, "");
}

export function GastoIa({ canManageAccounts, canManageRoles }: { canManageAccounts: boolean; canManageRoles: boolean }) {
  const [user, setUser] = useState("");
  const [kind, setKind] = useState("");
  const [tool, setTool] = useState("");
  const [groupBy, setGroupBy] = useState<"session" | "work" | "user">("session");
  const [data, setData] = useState<PageData | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<"user" | "kind" | "tool" | null>(null);
  const [error, setError] = useState(false);
  const [openGroup, setOpenGroup] = useState<string | null>(null);

  const query = useMemo(() => {
    const params = new URLSearchParams({ groupBy });
    if (user) params.set("user", user);
    if (kind) params.set("kind", kind);
    if (tool) params.set("tool", tool);
    return params;
  }, [user, kind, tool, groupBy]);

  const load = useCallback(async (next: string | null, append: boolean) => {
    setLoading(true);
    setError(false);
    if (!append) { setData(null); setGroups([]); setOpenGroup(null); }
    try {
      const params = new URLSearchParams(query);
      if (next) params.set("cursor", next);
      const response = await fetch(`/api/admin/gasto?${params}`, { cache: "no-store" });
      if (!response.ok) throw new Error("gasto fetch failed");
      const result = await response.json() as PageData;
      setData(result);
      setGroups((current) => append ? [...current, ...result.groups] : result.groups);
      setCursor(result.nextCursor);
      if (!append) setOpenGroup(result.groups[0]?.key ?? null);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
      setActiveFilter(null);
    }
  }, [query]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(null, false); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  function clearFilters() {
    setUser(""); setKind(""); setTool("");
  }

  return (
    <main className="mx-auto w-full min-w-0 max-w-7xl flex-1 px-5 py-8 sm:px-7 lg:px-10" lang="es">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-texto">Gasto de IA</h1>
        <Link href="/" className="ui-button-gh
```

## Resolution request ae405794f9e8c98682e388a7740da9f6 (src/lib/ia/nucleo/python-adapter.ts)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/ae405794f9e8c98682e388a7740da9f6.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/ae405794f9e8c98682e388a7740da9f6.diff3`
- blobs: base `d6383c58f0f2254a314a6ee7d7a4728057a2a38b`, ours `a10c17c6cb9d2f08ce6816f8a023c06a6c38fc2d`, theirs `9af991f967284fc706fe0d3b7703b8b2f417fe84` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "7042b3ba371b48ba11ce556009d7b489c478b25e", "ours": "7514afd0c0904f5e33ccccfb9746e9b322215e2c", "theirs": "217e5e5053d0497c4867ff21dae3c33e3fd8170a"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/ae405794f9e8c98682e388a7740da9f6.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
import {
  DEADLINE_DEFAULT_MS,
  DEADLINE_MAX_MS,
  InternalRequestSignatureV1Schema,
  OperationalContextV1Schema,
  crearDeadlineSignal,
  firmarRequestInterna,
  sha256Body,
} from "@/lib/ia/contracts/operational-v1";
import {
  CATALOG_COLORS_CONTRACT_VERSION,
  CATALOG_RECOMMENDATIONS_CONTRACT_VERSION,
  CatalogColorsResultV1Schema,
  CatalogRecommendationsResultV1Schema,
  ESTIMAR_CONTEO_CONTRACT_VERSION,
  EstimarConteoResultV1Schema,
  PlanResolutionResultV1Schema,
  type EstimarConteoRequestV1,
  type EstimarConteoResultV1,
} from "@/lib/ia/contracts/domain-v1";
import { ListaMaterialesResultadoSchema, ListaMaterialesRequestSchema } from "@/lib/ia/contracts/asistente-guiado-v1";
import {
  ArmadoBouquetResueltoSchema,
  DISPOSICIONES_NUMERO,
  LecturaArmadoSchema,
  VARIANTES_BOUQUET,
  type ArmadoBouquetResuelto,
  type ArmadoBouquetV1,
  type PistaArmado,
} from "@/lib/plan/armado-bouquet";
import {
  ArmadoGuirnaldaResueltoSchema,
  LecturaGuirnaldaSchema,
  type ArmadoGuirnaldaResuelto,
  type ArmadoGuirnaldaV1,
  type PistaGuirnalda,
} from "@/lib/plan/armado-guirnalda";
import {
  ArcoResueltoSchema,
  ArmadoArcoV1Schema,
  VistaArcoSchema,
  type ArcoResuelto,
  type ArmadoArcoV1,
  type VistaArco,
} from "@/lib/plan/armado-arco";
import { OpcionesArmadoGuirnaldaSchema, type OpcionesArmadoGuirnalda } from "@/lib/plan/opciones-armado-guirnalda";
import { GraficaDibujoEstructuraSchema, type GraficaDibujoEstructura } from "@/lib/plan/dibujo-estructura";
import { PLAN_GUIA_ESCENA_CONTRACT_VERSION, PlanGuiaEscenaRequestV1Schema, PlanGuiaEscenaResultV1Schema, type PlanGuiaEscenaRequestV1, type PlanGuiaEscenaResultV1 } from "@/lib/plan/guia-escena";
import {
  LimitesArcoSchema,
  OpcionesArmadoArcoSchema,
  type LimitesArco,
  type OpcionesArmadoArco,
} from "@/lib/plan/opciones-armado-arco";
import {
  ArcoOrganicoResueltoSchema,
  ArmadoArcoOrganicoV1Schema,
  type ArcoOrganicoResuelto,
  type ArmadoArcoOrganicoV1,
} from "@/lib/plan/armado-arco-organico";
import {
  LimitesArcoOrganicoSchema,
  OpcionesArmadoArcoOrganicoSchema,
  VistaArcoOrganicoSchema,
  type LimitesArcoOrganico,
  type OpcionesArmadoArcoOrganico,
  type VistaArcoOrganico,
} from "@/lib/plan/opciones-armado-arco-organico";
import {
  ArmadoColumnaOrganicaV1Schema,
  ColumnaOrganicaResueltaSchema,
  type ArmadoColumnaOrganicaV1,
  type ColumnaOrganicaResuelta,
} from "@/lib/plan/armado-columna-organica";
import {
  LimitesColumnaOrganicaSchema,
  OpcionesArmadoColumnaOrganicaSchema,
  VistaColumnaOrganicaSchema,
  type LimitesColumnaOrganica,
  type OpcionesArmadoColumnaOrganica,
  type VistaColumnaOrganica,
} from "@/lib/plan/opciones-armado-columna-organica";
import {
  ArmadoGuirnaldaOrganicaV1Schema,
  GuirnaldaOrganicaResueltaSchema,
  type ArmadoGuirnaldaOrganicaV1,
  type GuirnaldaOrganicaResuelta,
} from "@/lib/plan/armado-guirnalda-organica";
import {
  LimitesGuirnaldaOrganicaSchema,
  OpcionesArmadoGuirnaldaOrganicaSchema,
  VistaGuirnaldaOrganicaSchema,
  type LimitesGuirnaldaOrganica,
  type OpcionesArmadoGuirnaldaOrganica,
  type VistaGuirnaldaOrganica,
} from "@/lib/plan/opciones-armado-guirnalda-organica";
import {
  ArmadoCompletadoSchema,
  ArmadoDeIaSchema,
  CatalogoArmadoSchema,
  type AdornosPedidos,
  type ArmadoCompletado,
  type ArmadoDeIa,
  type CatalogoArmado,
  type ColorPedido,
  type FormaPedida,
  type GeometriaPedida,
  type PesoTamano,
  type PiezaArmado,
  type RematePedido,
  type TipoArmadoMotor,
  type VolumenPedido,
} from "@/lib/plan/armado-estructura-ia";
import { ArmadoColumnaV1Schema, ColumnaResueltaSchema, RemateLeidoSchema, VistaColumnaSchema, type ArmadoColumnaV1, type ColumnaResuelta, type PistaRemate, type VistaColumna } from "@/lib/plan/armado-columna";
import { LimitesColumnaSchema, OpcionesArmadoColumnaSchema, type LimitesColumna, type OpcionesArmadoColumna } from "@/lib/plan/opciones-armado-columna";
import { LecturaConteoSchema, type PistaConteo } from "@/lib/plan/conteo-referencia";
import type { PistaGeometria } from "@/lib/plan/geometria-referencia";
import type { EdicionPlan } from "@/lib/plan/edicion-esquemas";
import { CABECERA_MODOS_MATERIALES, CotizacionProfesionalResultadoSchema, type CotizacionProfesionalResultado, type EntradaCotizacionProfesional } from "@/lib/cotizacion/profesional";
import {
  MODOS_PATRON_COLOR,
  ModoAdmitidoSchema,
  PatronColorResueltoSchema,
  PistaPatronSchema,
  TAMANOS_LEIDOS,
  type ModoAdmitido,
  type ModoPatronColor,
  type PatronColor,
  type PatronColorResuelto,
  type PistaPatron,
  type PistaTamanos,
} from "@/lib/plan/patron-color";
import { PlanDecoracionSchema, type PlanDecoracion } from "@/lib/plan/tipos";
import type { PlanResuelto } from "@/lib/plan/resuelto";
import { cabecerasCorrelacion, crearFetchAuditado } from "@/lib/registro/servidor";
<<<<<<< ours (src/lib/ia/nucleo/python-adapter.ts)
import { contextoUsoDeOperacion, type PythonUsageContextPolicy } from "./python-adapter/usage-context";
||||||| base
=======
import { contextoUsoInternoActual } from "./contexto-uso-interno";
>>>>>>> theirs
import { z } from "zod";
import type { PythonChatTurnLanguage } from "@/lib/ia/nucleo/python-adapter/idioma";
import { campoIdiomaChatTurn } from "@/lib/ia/nucleo/python-adapter/idioma";

export const PYTHON_ECHO_PATH = "/internal/v1/echo";
export const PYTHON_ECHO_SCOPE = "ai.echo";
export const PYTHON_RERANK_PATH = "/internal/v1/rerank";
export const PYTHON_RERANK_SCOPE = "ai.rerank";
export const PYTHON_EMBEDDING_PATH = "/internal/v1/embed";
export const PYTHON_EMBEDDING_SCOPE = "ai.embedding";
export const PYTHON_CATALOG_SEARCH_PATH = "/internal/v1/catalog/search";
export const PYTHON_CATALOG_SEARCH_SCOPE = "catalog.search";
export const PYTHON_CATALOG_COLORS_PATH = "/internal/v1/catalog/colors";
export const PYTHON_CATALOG_COLORS_SCOPE = "catalog.colors";
export const PYTHON_CATALOG_SELECTION_PATH = "/internal/v1/catalog/selection";
export const PYTHON_CATALOG_SELECTION_SCOPE = "catalog.selection";
export const PYTHON_PLAN_RESOLUTION_PATH = "/internal/v1/plan/resolve";
export const PYTHON_PLAN_RESOLUTION_SCOPE = "plan.resolve";
export const PYTHON_CATALOG_RECOMMENDATIONS_PATH = "/internal/v1/catalog/recommendations";
export const PYTHON_CATALOG_RECOMMENDATIONS_SCOPE = "catalog.recommendations";
export const PYTHON_INTENT_PARSE_PATH = "/internal/v1/ia/intent-parse";
export const PYTHON_INTENT_PARSE_SCOPE = "ia.intent_parse";
export const PYTHON_HAPPIE_GENERATE_PATH = "/internal/v1/ia/happie-generate";
export const PYTHON_HAPPIE_GENERATE_SCOPE = "ia.happie_generate";
export const PYTHON_REFERENCE_TURN_PATH = "/internal/v1/ia/reference-turn";
export const PYTHON_REFERENCE_TURN_SCOPE = "ia.reference_turn";
export const PYTHON_FLUX_GENERATE_PATH = "/internal/v1/ia/lora-generate";
export const PYTHON_FLUX_GENERATE_SCOPE = "ia.lora_generate";
export const PYTHON_CHAT_TURN_STREAM_PATH = "/internal/v1/ia/chat-turn-stream";
export const PYTHON_CHAT_TURN_STREAM_SCOPE = "ia.chat_turn_stream";
export const PYTHON_PATRON_REFERENCIA_PATH = "/internal/v1/ia/patron-referencia";
export const PYTHON_PATRON_REFERENCIA_SCOPE = "ia.patron_referencia";
export const PYTHON_BOUQUET_REFERENCIA_PATH = "/internal/v1/ia/bouquet-referencia";
export const PYTHON_BOUQUET_REFERENCIA_SCOPE = "ia.bouquet_referencia";
export const PYTHON_CONTEO_REFERENCIA_PATH = "/internal/v1/ia/conteo-referencia";
export const PYTHON_CONTEO_REFERENCIA_SCOPE = "ia.conteo_referencia";
export const PYTHON_GUIRNALDA_REFERENCIA_PATH = "/internal/v1/ia/guirnalda-referencia";
export const PYTHON_GUIRNALDA_REFERENCIA_SCOPE = "ia.guirnalda_referencia";
export const PYTHON_LECTURA_UNICA_PATH = "/internal/v1/ia/lectura-unica";
export const PYTHON_LECTURA_UNICA_SCOPE = "ia.lectura_unica";
export const PYTHON_PLAN_EDIT_PATH = "/internal/v1/plan/edit";
export const PYTHON_PLAN_EDIT_SCOPE = "plan.edit";
export const PYTHON_PLAN_PATRON_PATH = "/internal/v1/plan/patron";
export const PYTHON_PLAN_PATRON_SCOPE = "plan.patron";
export const PYTHON_PLAN_ARMADO_PATH = "/internal/v1/plan/armado-bouquet";
export const PYTHON_PLAN_ARMADO_SCOPE = "plan.armado_bouquet";
export const PYTHON_PLAN_ARMADO_GUIRNALDA_PATH = "/internal/v1/plan/armado-guirnalda";
export const PYTHON_PLAN_ARMADO_GUIRNALDA_SCOPE = "plan.armado_guirnalda";
export const PYTHON_PLAN_ARMADO_ARCO_PATH = "/internal/v1/plan/armado-arco";
export const PYTHON_PLAN_ARMADO_ARCO_SCOPE = "plan.armado_arco";
export const PYTHON_PLAN_ARMADO_COLUMNA_PATH = "/internal/v1/plan/armado-columna";
export const PYTHON_PLAN_ARMADO_COLUMNA_SCOPE = "plan.armado_columna";
/** The organic garland of the designer's engine. It does NOT replace PYTHON_PLAN_ARMADO_GUIRNALDA_PATH (ADR-0032, clusters and toppers): both coexist on the same piece. */
/** The organic arch of the designer's engine. It does NOT replace PYTHON_PLAN_ARMADO_ARCO_PATH (the pattern grid): both coexist on the same kind of piece, and a half arch is armed here with `forma.corte` below 1. */
export const PYTHON_PLAN_ARMADO_ARCO_ORGANICO_PATH = "/internal/v1/plan/armado-arco-organico";
export const PYTHON_PLAN_ARMADO_ARCO_ORGANICO_SCOPE = "plan.armado_arco_organico";
/** The organic column of the designer's engine. It does NOT replace PYTHON_PLAN_ARMADO_COLUMNA_PATH (the ring tower with patterns): both coexist on the same kind of piece. */
export const PYTHON_PLAN_ARMADO_COLUMNA_ORGANICA_PATH = "/internal/v1/plan/armado-columna-organica";
export const PYTHON_PLAN_ARMADO_COLUMNA_ORGANICA_SCOPE = "plan.armado_columna_organica";
export const PYTHON_PLAN_ARMADO_GUIRNALDA_ORGANICA_PATH = "/internal/v1/plan/armado-guirnalda-organica";
export const PYTHON_PLAN_ARMADO_GUIRNALDA_ORGANICA_SCOPE = "plan.armado_guirnalda_organica";
/** The schematic drawing of a piece no engine builds (the wall, the circular hoop, the balloon ceiling, the table centerpiece). It resolves no assembly and counts nothing. */
export const PYTHON_PLAN_DIBUJO_ESTRUCTURA_PATH = "/internal/v1/plan/dibujo-estructura";
export const PYTHON_PLAN_DIBUJO_ESTRUCTURA_SCOPE = "plan.dibujo_estructura";
/** The balloons of every structure of the plan as flat discs in meters, for the scene guide the image model receives instead of the reference photo. It places and counts nothing: it reads what the engines and the schematic drawings already placed. */
export const PYTHON_PLAN_GUIA_ESCENA_PATH = "/internal/v1/plan/guia-escena";
export const PYTHON_PLAN_GUIA_ESCENA_SCOPE = "plan.guia_escena";
export const PYTHON_OMOIKANE_ARMADO_PATH = "/internal/v1/omoikane/armado-estructura";
export const PYTHON_OMOIKANE_ARMADO_SCOPE = "omoikane.armado_estructura";
export const PYTHON_COTIZACION_PROFESIONAL_PATH = "/internal/v1/plan/cotizacion-profesional";
export const PYTHON_COTIZACION_PROFESIONAL_SCOPE = "plan.cotizacion_profesional";
export const PYTHON_LISTA_MATERIALES_PATH = "/internal/v1/plan/lista-materiales";
export const PYTHON_LISTA_MATERIALES_SCOPE = "plan.lista_materiales";
export const PYTHON_ESTIMAR_CONTEO_PATH = "/internal/v1/plan/estimar-conteo";

/**
 * Operaciones del Python que ejecutan un modelo y su propósito en la auditoría (src/lib/registro): esas
 * peticiones dejan además `llamada_ia`/`respuesta_ia` con el cuerpo completo. Las que ya audita su propio
 * envoltorio (chat-turn-stream y reference-turn con envolverChatPort, lora-generate con
 * auditarGeneracionImagen, happie-generate con envolverFuncionIa) no van aquí: saldrían duplicadas. Tampoco
 * lectura-unica: no llama a ningún modelo (valida lo que escribió el análisis); queda como evento `python`.
 */
const PROPOSITO_IA_PYTHON: ReadonlyArray<readonly [string, string]> = [
  ["/internal/v1/ia/intent-parse", "parser_intencion"],
  ["/internal/v1/ia/patron-referencia", "lectura_patron_foto"],
  ["/internal/v1/ia/bouquet-referencia", "lectura_bouquet_foto"],
  ["/internal/v1/ia/conteo-referencia", "conteo_foto"],
  ["/internal/v1/ia/guirnalda-referencia", "lectura_guirnalda_foto"],
  ["/internal/v1/embed", "embedding"],
  ["/internal/v1/rerank", "rerank_catalogo"],
];

function propositoIaPython(ruta: string): string | undefined {
  return PROPOSITO_IA_PYTHON.find(([sufijo]) => ruta.endsWith(sufijo))?.[1];
}
export const PYTHON_ESTIMAR_CONTEO_SCOPE = "plan.estimar_conteo";
export const PYTHON_EMBEDDING_MODEL = "gemini-embedding-2";
export const PYTHON_EMBEDDING_DIMENSIONS = 768;
export const PYTHON_MAX_BODY_BYTES = 64 * 1024;
/** Reference-image analysis (Amaterasu) only -- same 10MB cap Next already enforces client-side (LIMITE_CUERPO_ANALISIS_BYTES in analisis-http.ts). */
export const PYTHON_MAX_BODY_BYTES_IMAGENES = 11 * 1024 * 1024;
/** Omoikane's chat turn only -- just above the 25_000_000-byte body /api/chat/route.ts already accepts from the browser, so the same photos fit on the Next -> Python hop. */
export const PYTHON_MAX_BODY_BYTES_CHAT = 25 * 1024 * 1024;
/** Happie's package recommendation only -- it carries the active Happia catalog as JSON text (MAX_BODY_BYTES_HAPPIE in main.py). */
export const PYTHON_MAX_BODY_BYTES_HAPPIE = 4 * 1024 * 1024;

/**
 * Stable domain error codes reported by POST /internal/v1/plan/resolve
 * (services/ai-api/app/plan.py). They arrive as PythonAdapterError.domainCode
 * under the PYTHON_INVALID_REQUEST transport code. A plan with no catalog
 * coverage is NOT an error: the service answers 200 with
 * `plan_resuelto.sin_cobertura` populated. `allowlist_product_mismatch` means a
 * variant was paired with a product that does not own it in the snapshot.
 */
export const PYTHON_PLAN_RESOLUTION_DOMAIN_CODES = ["invalid_plan", "catalog_snapshot_not_found", "allowlist_product_mismatch"] as const;
export type PythonPlanResolutionDomainCode = (typeof PYTHON_PLAN_RESOLUTION_DOMAIN_CODES)[number];

/**
 * Stable domain error codes reported by POST /internal/v1/catalog/selection
 * (services/ai-api/app/catalog.py). Same transport as plan resolution.
 */
export const PYTHON_CATALOG_SELECTION_DOMAIN_CODES = ["allowlist_product_mismatch"] as const;
export type PythonCatalogSelectionDomainCode = (typeof PYTHON_CATALOG_SELECTION_DOMAIN_CODES)[number];

/**
 * Stable domain error codes reported by POST /internal/v1/catalog/recommendations
 * (services/ai-api/app/recommendations.py), under PYTHON_INVALID_REQUEST.
 */
export const PYTHON_CATALOG_RECOMMENDATIONS_DOMAIN_CODES = ["catalog_snapshot_not_found", "reference_variant_not_found"] as const;
export type PythonCatalogRecommendationsDomainCode = (typeof PYTHON_CATALOG_RECOMMENDATIONS_DOMAIN_CODES)[number];

/**
 * Stable domain error codes reported by POST /internal/v1/plan/edit
 * (services/ai-api/app/plan_edicion.py, ADR-0028 §9). They keep Python's HTTP
 * status (404, 409, 400 or 422), so they do not all classify as
 * PYTHON_INVALID_REQUEST: callers branch on `domainCode`. `patron_invalido`
 * carries `domainDetails` (structure, stable `motivo`, Spanish `mensaje`).
 */
export const PYTHON_PLAN_EDIT_DOMAIN_CODES = [
  "estructura_no_encontrada",
  "variante_objetivo_no_encontrada",
  "reparto_no_corresponde",
  "material_no_editable",
  "unico_material",
  "sin_participacion",
  "patron_activo",
  "patron_invalido",
  "armado_invalido",
  "invalid_plan",
] as const;
export type PythonPlanEditDomainCode = (typeof PYTHON_PLAN_EDIT_DOMAIN_CODES)[number];

/**
 * Stable domain error codes reported by POST /internal/v1/plan/armado-bouquet
 * (ADR-0030). Its `armado_invalido` also carries the styles and number
 * placements the purchase admits (`domainDetails.variantesAdmitidas`,
 * `disposicionesAdmitidas`).
 */
export const PYTHON_PLAN_ARMADO_DOMAIN_CODES = [
  "estructura_no_encontrada",
  "armado_invalido",
  "invalid_plan",
] as const;
export type PythonPlanArmadoDomainCode = (typeof PYTHON_PLAN_ARMADO_DOMAIN_CODES)[number];

/**
 * Stable domain error codes reported by POST /internal/v1/plan/armado-guirnalda
 * (ADR-0032). Its `armado_invalido` carries the structure, the stable
 * `motivo` and Python's `mensaje` (`domainDetails`), never the options: the
 * editor asks for them with `armado_guirnalda: null`.
 */
export const PYTHON_PLAN_ARMADO_GUIRNALDA_DOMAIN_CODES = PYTHON_PLAN_ARMADO_DOMAIN_CODES;

/**
 * Stable domain error codes reported by POST /internal/v1/plan/armado-arco
 * (ADR-0034). The same three as the garland's: its `armado_invalido` carries
 * the structure, the stable `motivo` and Python's `mensaje`
 * (`domainDetails`), and never the options -- the editor asks for them with
 * `armado_arco: null`.
 */
export const PYTHON_PLAN_ARMADO_ARCO_DOMAIN_CODES = PYTHON_PLAN_ARMADO_DOMAIN_CODES;

/**
 * Stable domain error codes reported by POST /internal/v1/plan/armado-columna
 * (ADR-0034, ADR-0035 step 3). The same three as the arch's: its
 * `armado_invalido` carries the structure, the stable `motivo` and Python's
 * `mensaje` (`domainDetails`), and never the options -- the editor asks for
 * them with `armado_columna: null`.
 */
export const PYTHON_PLAN_ARMADO_COLUMNA_DOMAIN_CODES = PYTHON_PLAN_ARMADO_DOMAIN_CODES;

/**
 * Stable domain error codes reported by POST
 * /internal/v1/plan/armado-guirnalda-organica (ADR-0034). The same three as
 * the arch's: its `armado_invalido` carries the structure, the stable
 * `motivo` and Python's `mensaje` (`domainDetails`), and never the options --
 * the editor asks for them with `armado_guirnalda_organica: null`.
 */
export const PYTHON_PLAN_ARMADO_GUIRNALDA_ORGANICA_DOMAIN_CODES = PYTHON_PLAN_ARMADO_DOMAIN_CODES;

/**
 * Stable domain error codes reported by POST
 * /internal/v1/plan/armado-columna-organica (ADR-0034). The same three as the
 * arch's: its `armado_invalido` carries the structure, the stable `motivo` and
 * Python's `mensaje` (`domainDetails`), and never the options -- the editor
 * asks for them with `armado_columna_organica: null`.
 */
export const PYTHON_PLAN_ARMADO_COLUMNA_ORGANICA_DOMAIN_CODES = PYTHON_PLAN_ARMADO_DOMAIN_CODES;

/**
 * Stable domain error codes reported by POST
 * /internal/v1/plan/armado-arco-organico (ADR-0034). The same three as the
 * classic arch's: its `armado_invalido` carries the structure, the stable
 * `motivo` and Python's `mensaje` (`domainDetails`), and never the options --
 * the editor asks for them with `armado_arco_organico: null`.
 */
export const PYTHON_PLAN_ARMADO_ARCO_ORGANICO_DOMAIN_CODES = PYTHON_PLAN_ARMADO_DOMAIN_CODES;

/**
 * Stable domain error codes reported by POST /internal/v1/omoikane/armado-estructura
 * (ADR-0034 §5, the chat agent's engine tools). `armado_invalido` is the only
 * one the model can act on, and it carries the stable `motivo` and Python's
 * `mensaje` (`domainDetails`) so the refusal that reaches the model says what
 * did not hold -- an unknown pattern, a color the piece does not have, a
 * pattern that needs more colors than the piece has.
 */
export const PYTHON_OMOIKANE_ARMADO_DOMAIN_CODES = ["armado_invalido", "invalid_plan"] as const;
export type PythonOmoikaneArmadoDomainCode = (typeof PYTHON_OMOIKANE_ARMADO_DOMAIN_CODES)[number];

/**
 * Stable domain error codes reported by POST /internal/v1/plan/estimar-conteo
 * (ADR-0038, the chat agent's read-only count estimate). Both carry
 * `domainDetails`: the candidate's label (as `estructuraId`), a stable `motivo`
 * and Python's Spanish `mensaje`, so the refusal that reaches the model says
 * which candidate failed and why. `candidato_invalido`: two candidates share a
 * label, an assembly does not belong to the piece's type, or more guirnaldas with
 * an assembly than one query admits; `armado_invalido`: the engine's gate rejected
 * the assembly; `invalid_request`: the body does not meet the contract (a 422 with
 * no details); `estimacion_ocupada` (HTTP 429): another estimate is running and the
 * route does not queue behind it -- the caller retries.
 */
export const PYTHON_ESTIMAR_CONTEO_DOMAIN_CODES = ["candidato_invalido", "armado_invalido", "invalid_request", "estimacion_ocupada"] as const;
export type PythonEstimarConteoDomainCode = (typeof PYTHON_ESTIMAR_CONTEO_DOMAIN_CODES)[number];

/**
 * Stable domain erro
```

## CG-9

Workflow `None` (None); state: `null`

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/CG-9.history.jsonl` (none yet)

## CG-9

Workflow `None` (None); state: `null`

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/CG-9.history.jsonl` (none yet)

## CG-9

Workflow `None` (None); state: `null`

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/CG-9.history.jsonl` (none yet)

## Run status

Run workflow `bt:pictures:REQ-021:r26`: PENDING; summary status running. Full status: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-085358-d06c/status.json`.

- T95: PENDING {"task_id": "T95", "state": "running", "attempt": "pictures-REQ-021-r26-T95-a1-d95630b1"}

## Composition gates

Composed: `{"CG-3": "C1", "CG-5": "C2"}`; rejected: `{"CG-6": "git_text_conflict", "CG-7": "git_text_conflict", "CG-8": "git_text_conflict", "CG-9": "git_text_conflict"}`. A composition that fails is tried again on later turns of the run loop (`COMPOSE_TURNS`) before the gate counts as rejected; the owner's `retry-task` of the gate task composes it again.

Last gate and line events (telemetry):
- gate_composed: {"gate": "CG-3", "state": "candidate", "candidate_id": "C1", "reason": ""}
- gate_composed: {"gate": "CG-5", "state": "candidate", "candidate_id": "C2", "reason": ""}
- gate_composed: {"gate": "CG-6", "state": "rejected", "candidate_id": "C3", "reason": "git_text_conflict"}
- gate_composed: {"gate": "CG-7", "state": "rejected", "candidate_id": "C4", "reason": "git_text_conflict"}
- gate_composed: {"gate": "CG-8", "state": "rejected", "candidate_id": "C5", "reason": "git_text_conflict"}
- gate_composed: {"gate": "CG-9", "state": "rejected", "candidate_id": "C6", "reason": "git_text_conflict"}

Known case (agents/solver.md): gate CG-6 is rejected. Fix the origin of its reason above (the composer, a merge rule, the environment or the plan), integrate the fix, then `uv run --project ~/dev/metodologia bt-durable retry-task pictures REQ-021 T96`: it reopens the ended run and composes CG-6 again.

Known case (agents/solver.md): gate CG-7 is rejected. Fix the origin of its reason above (the composer, a merge rule, the environment or the plan), integrate the fix, then `uv run --project ~/dev/metodologia bt-durable retry-task pictures REQ-021 T97`: it reopens the ended run and composes CG-7 again.

Known case (agents/solver.md): gate CG-8 is rejected. Fix the origin of its reason above (the composer, a merge rule, the environment or the plan), integrate the fix, then `uv run --project ~/dev/metodologia bt-durable retry-task pictures REQ-021 T98`: it reopens the ended run and composes CG-8 again.

Known case (agents/solver.md): gate CG-9 is rejected. Fix the origin of its reason above (the composer, a merge rule, the environment or the plan), integrate the fix, then `uv run --project ~/dev/metodologia bt-durable retry-task pictures REQ-021 T99`: it reopens the ended run and composes CG-9 again.

## Files

- requirement: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t` (SPEC.md, PLAN.md, PLAN.json, SPEC.es.md)
- the frozen plan this run executes: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/plan-revisions/PLAN.r26.json`
- project decisions: `/home/david/bitacora/pictures/DECISIONS.md`
- metodologia decisions: `/home/david/bitacora/metodologia/DECISIONS.md`
- day log: `/home/david/bitacora/pictures/2026-10/W5/2026-10-28.md`
- day log: `/home/david/bitacora/pictures/2026-10/W5/2026-10-29.md`
- day log: `/home/david/bitacora/metodologia/2026-10/W5/2026-10-29.md`
- day log: `/home/david/bitacora/metodologia/2026-10/W5/2026-10-30.md`
- diagnoses: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.diagnoses`; healing: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.durable-healing.json`; activity: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/.planning/activity.jsonl`; telemetry and attempts: `/home/david/bitacora/.state/durable`

## Commands

- run status: `uv run --project ~/dev/metodologia bt-durable status pictures REQ-021`
- engine journal: `journalctl --user -u bt-durable.service --since -3h --no-pager -o cat`
- answer a decision: `uv run --project ~/dev/metodologia bt-durable answer pictures REQ-021 <task> <request>@k<round> <action> --note "..." --by solver`
- the run's Planner: `python3 /home/david/dev/metodologia/skill/scripts/bt_agent_terminal.py tell-planner pictures REQ-021 "<change request>"`
- integrate a metodologia fix: `python3 ~/dev/metodologia/skill/scripts/bt_integrate.py --branch solver/20261030-085358-d06c --worktree /home/david/.local/share/bitacora-solver/pictures/20261030-085358-d06c/wt --title "<what> (D-NNN)" --session 20261030-085358-d06c --trailer "<your attribution line>"` (`--dry-run` first; `--help` for the steps)

## Your session

- session folder (REPORT.md, result.json, NOTES.md, inbox.jsonl): `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-085358-d06c`
- working folder (your worktree goes in `/home/david/.local/share/bitacora-solver/pictures/20261030-085358-d06c/wt`): `/home/david/.local/share/bitacora-solver/pictures/20261030-085358-d06c`
- trigger keys for result.json `handled`: pictures:REQ-021:r26:resolution:33917a4fe713f9d06f614144e4061848, pictures:REQ-021:r26:resolution:95e324edf1c0f6a2dfa846402a03e8fd, pictures:REQ-021:r26:resolution:ae405794f9e8c98682e388a7740da9f6
- keep NOTES.md current (what you found, what you changed, what is next): you may be restarted on another account and must be able to continue from your files.
