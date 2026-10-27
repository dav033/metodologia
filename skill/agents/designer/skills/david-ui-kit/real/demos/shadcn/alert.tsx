import { AlertCircle, CheckCircle2, Info, Undo2 } from "lucide-react";
import { Alert, AlertAction, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Example } from "@kit/demo";

export default function AlertDemo() {
  return (
    <>
      <Example title="Informativa">
        <Alert>
          <Info />
          <AlertTitle>Montaje confirmado</AlertTitle>
          <AlertDescription>El equipo llegará al Salón Aurora a las 7:00 a. m. para armar el arco de globos.</AlertDescription>
        </Alert>
      </Example>
      <Example title="Destructiva">
        <Alert variant="destructive">
          <AlertCircle />
          <AlertTitle>No se pudo reservar la fecha</AlertTitle>
          <AlertDescription>El salón ya tiene un evento el 14 de noviembre. Elige otra fecha o contacta a la coordinación.</AlertDescription>
        </Alert>
      </Example>
      <Example title="Con acción y sin icono">
        <div className="flex flex-col gap-3">
          <Alert>
            <CheckCircle2 />
            <AlertTitle>Pedido #1284 archivado</AlertTitle>
            <AlertDescription>Puedes recuperarlo durante los próximos 30 días.</AlertDescription>
            <AlertAction><Button size="sm" variant="outline"><Undo2 data-icon="inline-start" />Deshacer</Button></AlertAction>
          </Alert>
          <Alert>
            <AlertTitle>Solo título</AlertTitle>
            <AlertDescription>Sin icono, el texto ocupa todo el ancho de la alerta.</AlertDescription>
          </Alert>
        </div>
      </Example>
    </>
  );
}
