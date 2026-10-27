import { lazy, Suspense, useState } from "react";
import { Example } from "@kit/demo";

// next/navigation reads `process` at load time; the sandboxed frame has none, so load the component after shimming it.
const PageTransition = lazy(async () => {
  const g = globalThis as { process?: unknown };
  g.process ??= { env: {} };
  const m = await import("@/components/animate-ui/components/page-transition");
  return { default: m.PageTransition };
});

const tabs = ["Pedidos", "Clientes"] as const;
const effects = ["fade", "slide", "zoom"] as const;

export default function PageTransitionDemo() {
  const [tab, setTab] = useState<(typeof tabs)[number]>("Pedidos");
  const [effect, setEffect] = useState<(typeof effects)[number]>("slide");
  return (
    <>
      <Example title="Transición entre dos paneles (sin router: pageKey)">
        <div className="max-w-md">
          <div role="tablist" className="mb-3 flex gap-2">
            {tabs.map((t) => (
              <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium ${tab === t ? "bg-primary text-primary-foreground" : "border border-input text-foreground"}`}>{t}</button>
            ))}
          </div>
          <Suspense fallback={<div className="h-20 rounded-xl border border-input" />}>
          <PageTransition pageKey={tab} effect={effect} className="rounded-xl border border-input bg-card p-4 text-card-foreground">
            {tab === "Pedidos" ? (
              <div><h3 className="text-sm font-semibold">12 pedidos esta semana</h3><p className="mt-1 text-sm text-muted-foreground">Arco orgánico, centros de mesa y columnas para 3 eventos.</p></div>
            ) : (
              <div><h3 className="text-sm font-semibold">342 clientes</h3><p className="mt-1 text-sm text-muted-foreground">Valentina Ríos, Familia Gómez, Salón Aurora.</p></div>
            )}
          </PageTransition>
          </Suspense>
        </div>
      </Example>
      <Example title="Efecto">
        <div className="flex gap-2">
          {effects.map((e) => (
            <button key={e} onClick={() => setEffect(e)} aria-pressed={effect === e}
              className={`rounded-lg px-3 py-1.5 text-sm ${effect === e ? "bg-secondary text-secondary-foreground" : "border border-input text-foreground"}`}>{e}</button>
          ))}
        </div>
      </Example>
    </>
  );
}
