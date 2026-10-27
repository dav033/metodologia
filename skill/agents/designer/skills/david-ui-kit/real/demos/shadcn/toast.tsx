import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { Button } from "@/components/ui/button";
import { Example, Row } from "@kit/demo";

export default function ToastDemo() {
  return (
    <>
      <Toaster position="bottom-right" />
      <Example title="Tipos de aviso">
        <Row>
          <Button variant="outline" onClick={() => toast("Cotización enviada", { description: "Boda Martínez · 120 invitados" })}>Neutro</Button>
          <Button variant="outline" onClick={() => toast.success("Pedido confirmado", { description: "Se notificó al equipo de montaje." })}>Éxito</Button>
          <Button variant="outline" onClick={() => toast.error("No se pudo guardar", { description: "Revisa tu conexión e inténtalo de nuevo." })}>Error</Button>
        </Row>
      </Example>
      <Example title="Con acción">
        <Row>
          <Button
            onClick={() => toast("Evento eliminado", { description: "Cumpleaños de Sofía", action: { label: "Deshacer", onClick: () => toast.success("Evento restaurado") } })}
          >
            Eliminar evento
          </Button>
          <Button variant="secondary" onClick={() => toast.info("3 pedidos nuevos hoy")}>Informativo</Button>
        </Row>
      </Example>
    </>
  );
}
