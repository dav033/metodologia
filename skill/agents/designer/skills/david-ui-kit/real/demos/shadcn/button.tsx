import { Loader2, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Example, Row } from "@kit/demo";

export default function ButtonDemo() {
  return (
    <>
      <Example title="Variantes">
        <Row>
          <Button>Guardar cambios</Button>
          <Button variant="secondary">Secundario</Button>
          <Button variant="outline">Contorno</Button>
          <Button variant="ghost">Fantasma</Button>
          <Button variant="destructive">Eliminar</Button>
          <Button variant="link">Enlace</Button>
        </Row>
      </Example>
      <Example title="Tamaños e iconos">
        <Row>
          <Button size="sm">Pequeño</Button>
          <Button>Normal</Button>
          <Button size="lg"><Plus data-icon="inline-start" />Nuevo proyecto</Button>
          <Button size="icon" variant="outline" aria-label="Eliminar"><Trash2 /></Button>
        </Row>
      </Example>
      <Example title="Estados">
        <Row>
          <Button disabled>Deshabilitado</Button>
          <Button disabled><Loader2 className="animate-spin" data-icon="inline-start" />Guardando…</Button>
        </Row>
      </Example>
    </>
  );
}
