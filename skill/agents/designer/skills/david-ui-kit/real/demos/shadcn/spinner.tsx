import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { Example, Row } from "@kit/demo";

export default function SpinnerDemo() {
  return (
    <>
      <Example title="Tamaños">
        <Row className="gap-6">
          <Spinner className="size-4" />
          <Spinner className="size-6" />
          <Spinner className="size-8" />
          <Spinner className="size-12" />
        </Row>
      </Example>
      <Example title="En botones">
        <Row>
          <Button disabled><Spinner data-icon="inline-start" />Guardando pedido…</Button>
          <Button variant="outline" disabled><Spinner data-icon="inline-start" />Enviando cotización…</Button>
        </Row>
      </Example>
      <Example title="Estado de carga">
        <div className="flex items-center gap-3 rounded-lg border border-border p-4 text-sm text-muted-foreground">
          <Spinner className="size-5 text-primary" role="status" aria-label="Cargando" />
          Buscando salones disponibles…
        </div>
      </Example>
    </>
  );
}
