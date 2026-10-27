import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Example } from "@kit/demo";

export default function InputDemo() {
  return (
    <>
      <Example title="Estados básicos">
        <div className="flex max-w-sm flex-col gap-3">
          <Input placeholder="Nombre del cliente" aria-label="Nombre del cliente" />
          <Input defaultValue="Salón Aurora" aria-label="Salón" />
          <Input type="email" placeholder="correo@empresa.co" aria-label="Correo" />
        </div>
      </Example>
      <Example title="Deshabilitado y con error">
        <div className="flex max-w-sm flex-col gap-3">
          <Input disabled defaultValue="PED-1042" aria-label="Pedido" />
          <Input aria-invalid defaultValue="-3 globos" aria-label="Cantidad" />
          <p className="text-sm text-destructive">La cantidad debe ser mayor que cero.</p>
        </div>
      </Example>
      <Example title="Con icono y archivo">
        <div className="flex max-w-sm flex-col gap-3">
          <div className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input className="pl-8" placeholder="Buscar pedidos…" aria-label="Buscar pedidos" />
          </div>
          <Input type="file" aria-label="Adjuntar diseño" />
        </div>
      </Example>
    </>
  );
}
