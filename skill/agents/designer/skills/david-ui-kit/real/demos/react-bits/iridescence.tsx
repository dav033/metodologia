import * as React from "react";
import Iridescence from "@/components/react-bits/Iridescence";
import { Effect } from "@kit/effect";
import { Example } from "@kit/demo";

function useDark() {
  const [d, setD] = React.useState(() => document.documentElement.classList.contains("dark"));
  React.useEffect(() => {
    const o = new MutationObserver(() => setD(document.documentElement.classList.contains("dark")));
    o.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => o.disconnect();
  }, []);
  return d;
}

const fb = <div className="size-full bg-gradient-to-br from-primary/50 via-chart-2/40 to-chart-3/50" />;

export default function IridescenceDemo() {
  const dark = useDark();
  return (
    <>
      <Example title="Superficie iridiscente en WebGL (sigue al cursor)">
        <Effect className="h-72 overflow-hidden rounded-xl border border-input" fallback={fb}>
          <Iridescence color={dark ? [0.6, 0.45, 0.9] : [0.7, 0.5, 1]} mouseReact speed={0.8} />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="rounded-xl bg-background/80 px-6 py-4 text-center backdrop-blur">
              <h3 className="text-xl font-semibold">Colección Primavera</h3>
              <p className="text-sm text-muted-foreground">Globos metalizados en tonos perla</p>
            </div>
          </div>
        </Effect>
      </Example>
      <Example title="Con remolino al clic y más detalle">
        <Effect className="h-56 overflow-hidden rounded-xl border border-input" fallback={fb}>
          <Iridescence color={[0.3, 0.7, 0.8]} clickSwirl warp={0.6} />
        </Effect>
      </Example>
    </>
  );
}
