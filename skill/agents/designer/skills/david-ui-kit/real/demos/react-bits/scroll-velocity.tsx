import * as React from "react";
import ScrollVelocity from "@/components/react-bits/ScrollVelocity";
import { Effect } from "@kit/effect";
import { Example } from "@kit/demo";

const still = (
  <div className="flex h-72 flex-col justify-center gap-2 overflow-hidden rounded-xl border border-input bg-background text-3xl font-bold">
    <span className="whitespace-nowrap px-4">Globos · Arcos · Centros de mesa · Columnas ·</span>
    <span className="whitespace-nowrap px-4 text-primary">Eventos · Bodas · Cumpleaños ·</span>
  </div>
);

export default function ScrollVelocityDemo() {
  const ref = React.useRef<HTMLDivElement>(null);
  return (
    <>
      <Example title="Marquesina que acelera con el scroll (desplaza dentro del recuadro)">
        <Effect className="h-72 overflow-hidden rounded-xl border border-input bg-background" fallback={still}>
          <div ref={ref} className="h-72 overflow-y-auto">
            <div className="sticky top-0 z-10 bg-background/80 py-3 backdrop-blur">
              <ScrollVelocity scrollContainerRef={ref} texts={["Globos · Arcos · Centros de mesa ·", "Eventos · Bodas · Cumpleaños ·"]}
                velocity={60} className="text-3xl font-bold" skewWithVelocity={4} fadeEdges numCopies={4} />
            </div>
            <div className="space-y-3 p-4 text-sm text-muted-foreground">
              {Array.from({ length: 14 }, (_, i) => (
                <p key={i}>Pedido #{2040 + i} · Salón {["Aurora", "Jazmín", "Cumbre", "Mirador"][i % 4]} · {120 + i * 15} globos</p>
              ))}
            </div>
          </div>
        </Effect>
      </Example>
      <Example title="Con contorno alterno y pausa al pasar el cursor">
        <Effect className="overflow-hidden rounded-xl border border-input bg-background py-4"
          fallback={<div className="whitespace-nowrap px-4 py-4 text-4xl font-black text-primary">Reserva hoy · Reserva hoy ·</div>}>
          <ScrollVelocity texts={["Reserva hoy ·", "Cotiza gratis ·"]} velocity={40} outlineAlternate pauseOnHover
            className="text-4xl font-black" color="var(--primary)" numCopies={4} />
        </Effect>
      </Example>
    </>
  );
}
