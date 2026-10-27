import * as React from "react";
import AnimatedList from "@/components/react-bits/AnimatedList";
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

const pedidos = [
  { id: 1, title: "Arco orgánico · Salón Aurora", description: "Camila Reyes · 14 nov", meta: "$1.480.000" },
  { id: 2, title: "Centros de mesa × 12", description: "Eventos Altavista · 15 nov", meta: "$620.000" },
  { id: 3, title: "Columnas de globos metalizados", description: "Banco Andino · 16 nov", meta: "$930.000" },
  { id: 4, title: "Piñata gigante de látex", description: "Laura Gómez · 18 nov", meta: "$210.000" },
  { id: 5, title: "Decoración de bautizo", description: "Familia Ortiz · 20 nov", meta: "$540.000" },
  { id: 6, title: "Cascada de globos para vitrina", description: "Joyería Lumen · 22 nov", meta: "$380.000" },
  { id: 7, title: "Cumpleaños temático espacial", description: "Mateo Vargas · 23 nov", meta: "$760.000" },
];

export default function AnimatedListDemo() {
  const dark = useDark();
  const { reduced } = useMotionProfile();
  const [sel, setSel] = React.useState<string>("Ninguno");
  return (
    <>
      <Example title="Pedidos con navegación por teclado (flechas) y selección">
        <AnimatedList items={pedidos} theme={dark ? "dark" : "light"} accentColor={dark ? "#cba6f7" : "#7a2ee0"}
          animation={reduced ? "none" : "slide"} maxHeight={320} width="100%" frame enableArrowNavigation
          onItemSelect={(it) => setSel(typeof it === "string" ? it : String((it as { title: React.ReactNode }).title))} />
        <p className="mt-2 text-sm text-muted-foreground">Elegido: {sel}</p>
      </Example>
      <Example title="Lista simple de textos, sin marco">
        <AnimatedList items={["Cotización enviada", "Anticipo recibido", "Montaje programado", "Evento entregado"]}
          theme={dark ? "dark" : "light"} accentColor={dark ? "#cba6f7" : "#7a2ee0"} animation="fade" showGradients={false}
          width="100%" maxHeight={220} />
      </Example>
    </>
  );
}
