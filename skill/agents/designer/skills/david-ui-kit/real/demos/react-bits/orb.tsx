import * as React from "react";
import Orb from "@/components/react-bits/Orb";
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

export default function OrbDemo() {
  const dark = useDark();
  const fb = <div className="mx-auto size-56 rounded-full bg-gradient-to-br from-primary/70 to-chart-2/60" />;
  return (
    <>
      <Example title="Esfera luminosa (reacciona al cursor)">
        <Effect className="h-72 overflow-hidden rounded-xl border border-input bg-background" fallback={<div className="flex size-full items-center">{fb}</div>}>
          <Orb colors={dark ? ["#cba6f7", "#89b4fa", "#94e2d5"] : ["#7a2ee0", "#1858d8", "#13777d"]} backgroundColor={dark ? "#11111b" : "#faf7ff"} hoverIntensity={0.6} />
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span className="rounded-lg bg-background/80 px-4 py-2 text-sm font-medium">Asistente de pedidos</span>
          </div>
        </Effect>
      </Example>
      <Example title="Siempre activa, con pulso al clic">
        <Effect className="h-56 overflow-hidden rounded-xl border border-input bg-background" fallback={<div className="flex size-full items-center">{fb}</div>}>
          <Orb colors={dark ? ["#f9a98b", "#f38ba8"] : ["#c2410c", "#b4237f"]} backgroundColor={dark ? "#11111b" : "#faf7ff"} forceHoverState clickPulse />
        </Effect>
      </Example>
    </>
  );
}
