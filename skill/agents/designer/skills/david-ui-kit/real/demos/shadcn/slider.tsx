import * as React from "react";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Example } from "@kit/demo";

const cop = (n: number) => n.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

export default function SliderDemo() {
  const [guests, setGuests] = React.useState([120]);
  const [budget, setBudget] = React.useState([800000, 2500000]);
  return (
    <>
      <Example title="Invitados (arrastra o usa las flechas)">
        <div className="flex max-w-md flex-col gap-3">
          <div className="flex justify-between text-sm"><Label>Número de invitados</Label><span className="tabular-nums text-muted-foreground">{guests[0]}</span></div>
          <Slider value={guests} onValueChange={(v) => setGuests(Array.isArray(v) ? v : [v])} min={10} max={400} step={10} aria-label="Invitados" />
        </div>
      </Example>
      <Example title="Rango de presupuesto">
        <div className="flex max-w-md flex-col gap-3">
          <div className="flex justify-between text-sm tabular-nums text-muted-foreground"><span>{cop(budget[0])}</span><span>{cop(budget[1])}</span></div>
          <Slider value={budget} onValueChange={(v) => setBudget(v as number[])} min={200000} max={5000000} step={50000} />
        </div>
      </Example>
      <Example title="Vertical y deshabilitado">
        <div className="flex items-center gap-10">
          <div className="h-40"><Slider defaultValue={[60]} orientation="vertical" aria-label="Volumen" /></div>
          <div className="w-64"><Slider defaultValue={[40]} disabled aria-label="Bloqueado" /></div>
        </div>
      </Example>
    </>
  );
}
