import * as React from "react";
import ElectricBorder from "@/components/react-bits/ElectricBorder";
import { Effect } from "@kit/effect";
import { Example, Row } from "@kit/demo";

function useDark() {
  const [d, setD] = React.useState(() => document.documentElement.classList.contains("dark"));
  React.useEffect(() => {
    const o = new MutationObserver(() => setD(document.documentElement.classList.contains("dark")));
    o.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => o.disconnect();
  }, []);
  return d;
}

const Card = ({ title, text }: { title: string; text: string }) => (
  <div className="w-64 rounded-[inherit] bg-card p-5 text-card-foreground">
    <h3 className="text-lg font-semibold">{title}</h3>
    <p className="mt-1 text-sm text-muted-foreground">{text}</p>
  </div>
);
const still = (title: string, text: string) => <div className="inline-block rounded-2xl border-2 border-primary"><Card title={title} text={text} /></div>;

export default function ElectricBorderDemo() {
  const dark = useDark();
  const theme = dark ? "dark" : "light";
  return (
    <>
      <Example title="Borde eléctrico animado">
        <Row className="gap-8 p-3">
          <Effect className="inline-block" fallback={still("Pedido urgente", "Entrega mañana 8:00 a.m.")}>
            <ElectricBorder theme={theme} color={dark ? "#cba6f7" : "#7a2ee0"} borderRadius={16}>
              <Card title="Pedido urgente" text="Entrega mañana 8:00 a.m." />
            </ElectricBorder>
          </Effect>
          <Effect className="inline-block" fallback={still("Evento destacado", "Boda Jazmín · sábado")}>
            <ElectricBorder theme={theme} color={dark ? "#94e2d5" : "#13777d"} borderRadius={16} speed={1.5} chaos={0.6} interactive>
              <Card title="Evento destacado" text="Boda Jazmín · sábado" />
            </ElectricBorder>
          </Effect>
        </Row>
      </Example>
      <Example title="Desactivado (estado reposo)">
        <div className="p-3">
          <ElectricBorder theme={theme} active={false} color={dark ? "#cba6f7" : "#7a2ee0"} borderRadius={16}>
            <Card title="Pedido entregado" text="Sin alertas pendientes" />
          </ElectricBorder>
        </div>
      </Example>
    </>
  );
}
