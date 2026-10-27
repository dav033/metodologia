import { CopyButton, CopyButtonIcon } from "@animate-ui/react/primitives/buttons/copy";
import { Check, Copy } from "lucide-react";
import { Example, Row } from "@kit/demo";

const cls = "inline-flex items-center gap-2 rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground";

export default function CopyButtonDemo() {
  return (
    <>
      <Example title="Copiar código de pedido (el icono cambia al copiar)">
        <Row>
          <code className="rounded-md bg-muted px-2 py-1 text-sm text-foreground">PED-2048</code>
          <CopyButton content="PED-2048" aria-label="Copiar código de pedido" className={cls}>
            <CopyButtonIcon icon={<Copy className="size-4" />} copiedIcon={<Check className="size-4 text-success" />} />
            Copiar
          </CopyButton>
        </Row>
      </Example>
      <Example title="Estado copiado inicial">
        <CopyButton content="Salón Aurora, 14 de noviembre" defaultCopied delay={999999} aria-label="Copiar dirección" className={cls}>
          <CopyButtonIcon icon={<Copy className="size-4" />} copiedIcon={<Check className="size-4 text-success" />} />
          Dirección del evento
        </CopyButton>
      </Example>
    </>
  );
}
