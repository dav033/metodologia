import { Textarea } from "@/components/ui/textarea";
import { Example } from "@kit/demo";

export default function TextareaDemo() {
  return (
    <>
      <Example title="Por defecto">
        <Textarea className="max-w-md" placeholder="Describe la decoración del evento…" aria-label="Descripción" />
      </Example>
      <Example title="Con contenido">
        <Textarea className="max-w-md" rows={4} aria-label="Notas" defaultValue={"Arco orgánico en tonos lila y durazno.\nEntrega a las 14:00 en el Salón Aurora.\nContactar a Laura al llegar."} />
      </Example>
      <Example title="Error y deshabilitado">
        <div className="flex max-w-md flex-col gap-3">
          <Textarea aria-invalid aria-label="Motivo" defaultValue="Cancelar" />
          <p className="text-sm text-destructive">Explica el motivo con al menos 20 caracteres.</p>
          <Textarea disabled aria-label="Bloqueado" defaultValue="Pedido cerrado: no se puede editar." />
        </div>
      </Example>
    </>
  );
}
