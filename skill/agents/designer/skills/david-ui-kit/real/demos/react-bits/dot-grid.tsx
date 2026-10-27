import * as React from "react";
import DotGrid from "@/components/react-bits/DotGrid";
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

export default function DotGridDemo() {
  const dark = useDark();
  const base = dark ? "#45475a" : "#cbc3d9";
  const active = dark ? "#cba6f7" : "#7a2ee0";
  const fb = <div className="size-full opacity-60" style={{ backgroundImage: "radial-gradient(var(--border) 1.5px, transparent 1.5px)", backgroundSize: "20px 20px" }} />;
  return (
    <>
      <Example title="Rejilla de puntos que reacciona al cursor y al clic">
        <Effect className="h-72 overflow-hidden rounded-xl border border-input bg-background" fallback={fb}>
          <DotGrid baseColor={base} activeColor={active} dotSize={6} gap={20} clickShock />
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <p className="rounded-lg bg-background/80 px-4 py-2 text-sm font-medium">Mueve el cursor sobre la rejilla</p>
          </div>
        </Effect>
      </Example>
      <Example title="Puntos redondeados con brillo">
        <Effect className="h-56 overflow-hidden rounded-xl border border-input bg-background" fallback={fb}>
          <DotGrid baseColor={base} activeColor={dark ? "#94e2d5" : "#13777d"} dotSize={10} gap={28} shape="circle" glow={0.5} />
        </Effect>
      </Example>
    </>
  );
}
