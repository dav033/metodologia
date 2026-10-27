import * as React from "react";
import GooeyNav from "@/components/react-bits/GooeyNav";
import { Example } from "@kit/demo";
import { useMotionProfile } from "@kit/motion";

function useDark() {
  const [d, setD] = React.useState(() => document.documentElement.classList.contains("dark"));
  React.useEffect(() => {
    const o = new MutationObserver(() => setD(document.documentElement.classList.contains("dark")));
    o.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => o.disconnect();
  }, []);
  return d;
}

const items = [
  { label: "Inicio", href: "#inicio" }, { label: "Pedidos", href: "#pedidos" }, { label: "Clientes", href: "#clientes" },
  { label: "Eventos", href: "#eventos" }, { label: "Salones", href: "#salones" },
];

export default function GooeyNavDemo() {
  const dark = useDark();
  const { reduced } = useMotionProfile();
  const [active, setActive] = React.useState(0);
  return (
    <>
      <Example title="Navegación con burbuja líquida y partículas (flechas / Tab + Enter)">
        <GooeyNav items={items} theme={dark ? "dark" : "light"} frame particleCount={reduced ? 0 : 15}
          color={dark ? "#cba6f7" : "#7a2ee0"} onChange={(i) => setActive(i)} />
        <p className="mt-3 text-sm text-muted-foreground">Sección activa: {items[active].label}</p>
      </Example>
      <Example title="Tamaño pequeño, colores del tema, sin marco">
        <GooeyNav items={items.slice(0, 4)} size="sm" theme={dark ? "dark" : "light"} initialActiveIndex={2}
          colors={dark ? ["#cba6f7", "#89b4fa", "#94e2d5"] : ["#7a2ee0", "#1858d8", "#13777d"]} particleCount={reduced ? 0 : 8} />
      </Example>
    </>
  );
}
