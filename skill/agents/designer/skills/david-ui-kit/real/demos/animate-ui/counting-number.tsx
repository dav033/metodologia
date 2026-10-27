import { CountingNumber } from "@animate-ui/react/primitives/texts/counting-number";
import { Example, Row } from "@kit/demo";

export default function CountingNumberDemo() {
  return (
    <Example title="KPIs que cuentan al entrar en pantalla">
      <Row className="gap-10">
        {[["Pedidos", 1284], ["Clientes", 342], ["Globos", 58210]].map(([label, n]) => (
          <div key={label as string} className="flex flex-col gap-1">
            <span className="text-3xl font-semibold tabular-nums"><CountingNumber number={n as number} inView /></span>
            <span className="text-sm text-muted-foreground">{label}</span>
          </div>
        ))}
      </Row>
    </Example>
  );
}
