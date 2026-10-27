import "@fontsource-variable/fraunces/full.css";
import * as React from "react";
import VariableProximity from "@/components/react-bits/VariableProximity";
import { Effect } from "@kit/effect";
import { Example } from "@kit/demo";

const FONT = { fontFamily: "'Fraunces Variable', serif" };

export default function VariableProximityDemo() {
  const a = React.useRef<HTMLDivElement>(null);
  const b = React.useRef<HTMLDivElement>(null);
  return (
    <>
      <Example title="El grosor sigue al cursor (fuente variable local)">
        <Effect className="rounded-xl border border-input bg-background p-6"
          fallback={<p className="p-6 text-3xl font-black" style={FONT}>Un salón lleno de globos y color</p>}>
          <div ref={a} style={FONT} className="relative">
            <VariableProximity label="Un salón lleno de globos y color" containerRef={a} radius={110} falloff="gaussian"
              fromFontVariationSettings="'wght' 300, 'opsz' 9" toFontVariationSettings="'wght' 900, 'opsz' 144"
              className="text-4xl" />
          </div>
        </Effect>
      </Example>
      <Example title="Con color, elevación y onda en reposo">
        <Effect className="rounded-xl border border-input bg-background px-6 pb-6 pt-10"
          fallback={<p className="p-6 text-2xl font-bold text-primary" style={FONT}>Reserva tu fecha hoy</p>}>
          <div ref={b} style={FONT} className="relative">
            <VariableProximity label="Reserva tu fecha hoy" containerRef={b} radius={90} idleWave lift={4}
              fromColor="var(--foreground)" toColor="var(--primary)"
              fromFontVariationSettings="'wght' 400, 'opsz' 24" toFontVariationSettings="'wght' 900, 'opsz' 96"
              className="text-3xl" />
          </div>
        </Effect>
      </Example>
    </>
  );
}
