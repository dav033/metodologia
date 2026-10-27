import { Button } from "@animate-ui/react/primitives/buttons/button";
import { Example, Row } from "@kit/demo";

export default function AnimatedButtonDemo() {
  return (
    <>
      <Example title="Botón con escala al pasar y al presionar">
        <Row>
          <Button className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Confirmar pedido</Button>
          <Button className="rounded-lg border border-input bg-background px-4 py-2 text-sm font-medium text-foreground">Ver cliente</Button>
        </Row>
      </Example>
      <Example title="Escalas personalizadas y deshabilitado">
        <Row>
          <Button hoverScale={1.12} tapScale={0.9} className="rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground">Reservar salón</Button>
          <Button disabled className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">Evento cerrado</Button>
        </Row>
      </Example>
    </>
  );
}
