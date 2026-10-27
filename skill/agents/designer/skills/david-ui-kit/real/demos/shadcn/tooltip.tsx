import { Info, Printer, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Example, Row } from "@kit/demo";

export default function TooltipDemo() {
  return (
    <TooltipProvider>
      <Example title="Pasa el cursor o enfoca con Tab" className="min-h-28">
        <Row>
          <Tooltip defaultOpen>
            <TooltipTrigger render={<Button variant="outline" size="icon" aria-label="Imprimir ficha" />}><Printer /></TooltipTrigger>
            <TooltipContent>Imprimir ficha del pedido</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger render={<Button variant="outline" size="icon" aria-label="Eliminar" />}><Trash2 /></TooltipTrigger>
            <TooltipContent>Eliminar pedido</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger render={<Button variant="ghost" size="icon" aria-label="Información" />}><Info /></TooltipTrigger>
            <TooltipContent>Los globos se inflan el día del evento</TooltipContent>
          </Tooltip>
        </Row>
      </Example>
      <Example title="Posiciones" className="min-h-32">
        <Row>
          {(["top", "right", "bottom", "left"] as const).map((side) => (
            <Tooltip key={side}>
              <TooltipTrigger render={<Button variant="secondary" />}>{{ top: "Arriba", right: "Derecha", bottom: "Abajo", left: "Izquierda" }[side]}</TooltipTrigger>
              <TooltipContent side={side}>Salón Aurora</TooltipContent>
            </Tooltip>
          ))}
        </Row>
      </Example>
    </TooltipProvider>
  );
}
