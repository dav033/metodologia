import { Copy, Mail, Search, Send } from "lucide-react";
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput, InputGroupText, InputGroupTextarea } from "@/components/ui/input-group";
import { Spinner } from "@/components/ui/spinner";
import { Example } from "@kit/demo";

export default function InputGroupDemo() {
  return (
    <>
      <Example title="Iconos, texto y botones">
        <div className="flex max-w-md flex-col gap-3">
          <InputGroup>
            <InputGroupAddon><Search /></InputGroupAddon>
            <InputGroupInput placeholder="Buscar pedidos…" aria-label="Buscar pedidos" />
            <InputGroupAddon align="inline-end">12 resultados</InputGroupAddon>
          </InputGroup>
          <InputGroup>
            <InputGroupAddon><InputGroupText>$</InputGroupText></InputGroupAddon>
            <InputGroupInput placeholder="0" inputMode="numeric" aria-label="Presupuesto" />
            <InputGroupAddon align="inline-end"><InputGroupText>COP</InputGroupText></InputGroupAddon>
          </InputGroup>
          <InputGroup>
            <InputGroupInput defaultValue="https://globos.example/cotizacion/1284" readOnly aria-label="Enlace" />
            <InputGroupAddon align="inline-end">
              <InputGroupButton aria-label="Copiar enlace" size="icon-xs"><Copy /></InputGroupButton>
            </InputGroupAddon>
          </InputGroup>
        </div>
      </Example>
      <Example title="Área de texto con barra inferior">
        <InputGroup className="max-w-md">
          <InputGroupTextarea placeholder="Escribe una nota para el cliente…" aria-label="Nota" />
          <InputGroupAddon align="block-end">
            <InputGroupText>0 / 280</InputGroupText>
            <InputGroupButton variant="default" size="sm" className="ml-auto"><Send data-icon="inline-start" />Enviar</InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
      </Example>
      <Example title="Estados: cargando, inválido, deshabilitado">
        <div className="flex max-w-md flex-col gap-3">
          <InputGroup>
            <InputGroupInput defaultValue="valentina@correo.co" aria-label="Correo cargando" />
            <InputGroupAddon align="inline-end"><Spinner /></InputGroupAddon>
          </InputGroup>
          <InputGroup>
            <InputGroupAddon><Mail /></InputGroupAddon>
            <InputGroupInput defaultValue="valentina@correo" aria-invalid="true" aria-label="Correo inválido" />
          </InputGroup>
          <InputGroup>
            <InputGroupAddon><Mail /></InputGroupAddon>
            <InputGroupInput disabled placeholder="Correo del cliente" aria-label="Correo deshabilitado" />
          </InputGroup>
        </div>
      </Example>
    </>
  );
}
