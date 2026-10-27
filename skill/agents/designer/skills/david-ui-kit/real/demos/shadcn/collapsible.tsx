import * as React from "react";
import { ChevronDown } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { Example } from "@kit/demo";

export default function CollapsibleDemo() {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <Example title="Detalle del pedido (se despliega con animación)">
        <Collapsible open={open} onOpenChange={setOpen} className="flex max-w-md flex-col gap-2 rounded-lg border border-border p-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="font-medium">PED-1284 · Boda Martínez</p>
              <p className="text-sm text-muted-foreground">3 artículos</p>
            </div>
            <CollapsibleTrigger render={<Button variant="ghost" size="icon" aria-label="Mostrar detalle" />}>
              <ChevronDown className={`transition-transform ${open ? "rotate-180" : ""}`} />
            </CollapsibleTrigger>
          </div>
          <CollapsibleContent>
            <ul className="flex flex-col gap-2 border-t border-border pt-3 text-sm">
              <li className="flex justify-between"><span>Arco orgánico pastel</span><span className="tabular-nums">$ 980.000</span></li>
              <li className="flex justify-between"><span>420 globos de látex</span><span className="tabular-nums">$ 1.050.000</span></li>
              <li className="flex justify-between"><span>Letras foil “AMOR”</span><span className="tabular-nums">$ 420.000</span></li>
            </ul>
          </CollapsibleContent>
        </Collapsible>
      </Example>
      <Example title="Abierto por defecto y deshabilitado">
        <div className="flex max-w-md flex-col gap-3">
          <Collapsible defaultOpen className="rounded-lg border border-border p-3">
            <CollapsibleTrigger render={<Button variant="link" className="px-0" />}>Notas de montaje</CollapsibleTrigger>
            <CollapsibleContent>
              <p className="pt-2 text-sm text-muted-foreground">Acceso por la puerta lateral. El técnico de luces llega a las 6:30 a. m.</p>
            </CollapsibleContent>
          </Collapsible>
          <Collapsible disabled className="rounded-lg border border-border p-3">
            <CollapsibleTrigger render={<Button variant="link" className="px-0" disabled />}>Historial (sin cambios)</CollapsibleTrigger>
            <CollapsibleContent><p className="pt-2 text-sm">Sin contenido.</p></CollapsibleContent>
          </Collapsible>
        </div>
      </Example>
    </>
  );
}
