import * as React from "react";
import Aurora from "@/components/react-bits/Aurora";
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

const fb = <div className="size-full bg-gradient-to-b from-primary/40 via-chart-2/30 to-transparent" />;

export default function AuroraDemo() {
  const dark = useDark();
  return (
    <>
      <Example title="Fondo de héroe en WebGL (reacciona al cursor)">
        <Effect className="h-72 overflow-hidden rounded-xl border border-input bg-background" fallback={fb}>
          <Aurora colorStops={dark ? ["#cba6f7", "#89b4fa", "#94e2d5"] : ["#7a2ee0", "#1858d8", "#13777d"]} lightMode={!dark} amplitude={1} speed={0.8} mouseInteraction />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="rounded-xl bg-background/80 px-6 py-4 text-center backdrop-blur">
              <h3 className="text-xl font-semibold">Tu evento empieza aquí</h3>
              <p className="text-sm text-muted-foreground">Decoración con globos para cada ocasión</p>
            </div>
          </div>
        </Effect>
      </Example>
      <Example title="Paleta cálida, desde abajo">
        <Effect className="h-56 overflow-hidden rounded-xl border border-input bg-background" fallback={fb}>
          <Aurora colorStops={dark ? ["#f9a98b", "#f38ba8", "#cba6f7"] : ["#c2410c", "#b4237f", "#7a2ee0"]} lightMode={!dark} direction="bottom" amplitude={0.8} />
        </Effect>
      </Example>
    </>
  );
}
