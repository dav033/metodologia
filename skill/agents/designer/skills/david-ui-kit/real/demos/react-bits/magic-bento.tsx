import * as React from "react";
import MagicBento from "@/components/react-bits/MagicBento";
import { Effect } from "@kit/effect";
import { Example } from "@kit/demo";

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
  { id: 1, label: "Pedidos", title: "1.284 pedidos", description: "Este año, 18% más que el anterior", visual: "analytics" as const, colSpan: 2 },
  { id: 2, label: "Clientes", title: "342 clientes", description: "Empresas y familias recurrentes", visual: "collaboration" as const },
  { id: 3, label: "Calendario", title: "Eventos del mes", description: "27 montajes programados", visual: "dashboard" as const },
  { id: 4, label: "Taller", title: "Producción", description: "Armado automatizado de arcos", visual: "integration" as const },
  { id: 5, label: "Pagos", title: "Anticipos", description: "Cobro seguro con enlace", visual: "security" as const, colSpan: 2 },
];

export default function MagicBentoDemo() {
  const dark = useDark();
  const theme = dark ? "dark" : "light";
  const glow = dark ? "#cba6f7" : "#7a2ee0";
  return (
    <>
      <Example title="Bento con brillo en bordes, destello y estrellas (mueve el cursor)">
        <Effect className="overflow-hidden rounded-xl"
          fallback={<MagicBento items={items} columns={3} theme={theme} glowColor={glow} disableAnimations enableStars={false} enableSpotlight={false} enableTilt={false} />}>
          <MagicBento items={items} columns={3} rowHeight={220} theme={theme} glowColor={glow} enableBorderGlow enableSpotlight
            enableStars particleCount={8} enableTilt={false} clickEffect />
        </Effect>
      </Example>
      <Example title="Con inclinación y magnetismo">
        <Effect className="overflow-hidden rounded-xl"
          fallback={<MagicBento items={items.slice(0, 3)} columns={3} theme={theme} glowColor={glow} disableAnimations />}>
          <MagicBento items={items.slice(0, 3)} columns={3} rowHeight={220} theme={theme} glowColor={glow} enableTilt enableMagnetism
            enableStars={false} />
        </Effect>
      </Example>
    </>
  );
}
