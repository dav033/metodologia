import * as React from "react";
import { Switch } from "@/components/ui/switch";
import { Example, Row } from "@kit/demo";

export default function SwitchDemo() {
  const [on, setOn] = React.useState(true);
  return (
    <>
      <Example title="Notificaciones (acciona para ver el deslizamiento)">
        <div className="flex flex-col gap-3">
          <label className="flex items-center gap-3 text-sm">
            <Switch checked={on} onCheckedChange={setOn} />
            Avisar al cliente cuando el pedido salga ({on ? "activado" : "desactivado"})
          </label>
          <label className="flex items-center gap-3 text-sm"><Switch /> Recordatorio 24 h antes</label>
        </div>
      </Example>
      <Example title="Tamaño pequeño y estados">
        <Row className="gap-6">
          <label className="flex items-center gap-2 text-sm"><Switch size="sm" defaultChecked /> Pequeño</label>
          <label className="flex items-center gap-2 text-sm"><Switch disabled /> Deshabilitado</label>
          <label className="flex items-center gap-2 text-sm"><Switch disabled defaultChecked /> Bloqueado activo</label>
        </Row>
      </Example>
    </>
  );
}
