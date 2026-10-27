import * as React from "react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Example } from "@kit/demo";

const plans = [
  { value: "basico", title: "Básico", desc: "Arco de 100 globos, 1 color" },
  { value: "premium", title: "Premium", desc: "Arco orgánico, foil y luces" },
  { value: "gala", title: "Gala", desc: "Montaje completo del salón" },
];

export default function RadioGroupDemo() {
  const [plan, setPlan] = React.useState("premium");
  return (
    <>
      <Example title="Selecciona un paquete (el indicador se anima al cambiar)">
        <div className="flex flex-col gap-3">
          <RadioGroup value={plan} onValueChange={(v) => setPlan(String(v))} className="max-w-sm">
            {plans.map((p) => (
              <Label key={p.value} htmlFor={`plan-${p.value}`} className="flex cursor-pointer items-start gap-3 rounded-lg border border-border p-3 has-data-checked:border-primary">
                <RadioGroupItem id={`plan-${p.value}`} value={p.value} className="mt-0.5" />
                <span className="flex flex-col gap-0.5">
                  <span className="font-medium">{p.title}</span>
                  <span className="text-sm font-normal text-muted-foreground">{p.desc}</span>
                </span>
              </Label>
            ))}
          </RadioGroup>
          <p className="text-sm text-muted-foreground">Paquete elegido: {plans.find((p) => p.value === plan)?.title}</p>
        </div>
      </Example>
      <Example title="Simple, horizontal y deshabilitado">
        <div className="flex flex-col gap-4">
          <RadioGroup defaultValue="tarde" className="flex w-auto gap-5">
            {["Mañana", "Tarde", "Noche"].map((t) => (
              <div key={t} className="flex items-center gap-2">
                <RadioGroupItem id={`t-${t}`} value={t.toLowerCase()} />
                <Label htmlFor={`t-${t}`}>{t}</Label>
              </div>
            ))}
          </RadioGroup>
          <RadioGroup defaultValue="a" disabled>
            <div className="flex items-center gap-2"><RadioGroupItem id="d-a" value="a" /><Label htmlFor="d-a">Retiro en bodega</Label></div>
            <div className="flex items-center gap-2"><RadioGroupItem id="d-b" value="b" /><Label htmlFor="d-b">Entrega en el salón</Label></div>
          </RadioGroup>
        </div>
      </Example>
    </>
  );
}
