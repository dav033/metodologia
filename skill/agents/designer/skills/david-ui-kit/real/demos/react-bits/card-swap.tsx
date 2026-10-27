import * as React from "react";
import CardSwap, { Card } from "@/components/react-bits/CardSwap";
import { Effect } from "@kit/effect";
import { Example, picture } from "@kit/demo";

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
  { title: "Salón Aurora", image: picture("Salón Aurora", 280, 480, 300), alt: "Salón Aurora" },
  { title: "Arco orgánico", image: picture("Arco orgánico", 200, 480, 300), alt: "Arco orgánico" },
  { title: "Boda Jazmín", image: picture("Boda Jazmín", 330, 480, 300), alt: "Boda Jazmín" },
];

export default function CardSwapDemo() {
  const theme = useDark() ? "dark" : "light";
  return (
    <>
      <Example title="Pila que rota sola (se pausa al pasar el cursor)">
        <Effect className="h-96 overflow-hidden rounded-xl border border-input bg-background"
          fallback={<div className="flex size-full items-center justify-center"><img src={items[0].image} alt={items[0].alt} className="h-56 rounded-xl" /></div>}>
          <CardSwap items={items} width={340} height={220} theme={theme} autoplay delay={3000} pauseOnHover />
        </Effect>
      </Example>
      <Example title="Con tarjetas propias, manual (arrastra para cambiar)">
        <Effect className="h-96 overflow-hidden rounded-xl border border-input bg-background"
          fallback={<div className="flex size-full items-center justify-center p-6 text-lg font-medium">Cotiza · Diseña · Monta</div>}>
          <CardSwap width={340} height={220} theme={theme} autoplay={false} draggable>
            {["Cotiza", "Diseña", "Monta"].map((t, i) => (
              <Card key={t}><div className="flex size-full flex-col justify-end p-5"><span className="text-xs opacity-70">Paso {i + 1}</span><span className="text-2xl font-semibold">{t}</span></div></Card>
            ))}
          </CardSwap>
        </Effect>
      </Example>
    </>
  );
}
