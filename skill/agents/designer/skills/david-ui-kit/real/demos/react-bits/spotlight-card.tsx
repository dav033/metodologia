import * as React from "react";
import SpotlightCard from "@/components/react-bits/SpotlightCard";
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

export default function SpotlightCardDemo() {
  const dark = useDark();
  const theme = dark ? "dark" : "light";
  return (
    <>
      <Example title="Foco que sigue al cursor">
        <Row className="items-stretch gap-4">
          <SpotlightCard theme={theme} spotlightColor={dark ? "#cba6f7" : "#7a2ee0"} className="w-72 p-6">
            <h3 className="text-lg font-semibold">Evento corporativo</h3>
            <p className="mt-1 text-sm opacity-80">Lanzamiento de producto · 180 invitados · Salón Cumbre.</p>
          </SpotlightCard>
          <SpotlightCard theme={theme} shape="beam" spotlightColor={dark ? "#89b4fa" : "#1858d8"} borderGlow={0.6} className="w-72 p-6">
            <h3 className="text-lg font-semibold">Boda</h3>
            <p className="mt-1 text-sm opacity-80">Arco orgánico y columnas · 120 invitados · Jardín Jazmín.</p>
          </SpotlightCard>
        </Row>
      </Example>
      <Example title="Con grano y destello ambiental">
        <SpotlightCard theme={theme} ambient flare grain={0.3} spotlightColor={dark ? "#f9a98b" : "#c2410c"} className="max-w-md p-6">
          <h3 className="text-lg font-semibold">Cumpleaños infantil</h3>
          <p className="mt-1 text-sm opacity-80">Tema espacial, 60 globos metalizados y piñata gigante.</p>
        </SpotlightCard>
      </Example>
    </>
  );
}
