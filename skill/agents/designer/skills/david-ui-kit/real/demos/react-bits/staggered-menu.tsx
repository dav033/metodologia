import StaggeredMenu from "@/components/react-bits/StaggeredMenu";
import * as React from "react";
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

const logo = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(
  "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='32'><rect width='160' height='32' rx='8' fill='white'/><circle cx='18' cy='16' r='11' fill='#7a2ee0'/><circle cx='30' cy='12' r='7' fill='#b4237f'/><text x='46' y='22' font-family='system-ui,sans-serif' font-size='17' font-weight='700' fill='#7a2ee0'>Globos&amp;Co</text></svg>");

const items = [
  { label: "Inicio", ariaLabel: "Ir al inicio", link: "#inicio" },
  { label: "Pedidos", ariaLabel: "Ver pedidos", link: "#pedidos" },
  { label: "Clientes", ariaLabel: "Ver clientes", link: "#clientes" },
  { label: "Contacto", ariaLabel: "Contactar", link: "#contacto" },
];
const socials = [{ label: "Instagram", link: "#ig" }, { label: "WhatsApp", link: "#wa" }];

export default function StaggeredMenuDemo() {
  const btn = useDark() ? "#ffffff" : "#18181b";
  return (
    <>
      <Example title="Menú lateral derecho (pulsa Menú; Esc o clic fuera lo cierra)">
        <div className="relative h-96 overflow-hidden rounded-xl border border-input bg-muted">
          <StaggeredMenu isFixed={false} position="right" items={items} socialItems={socials} logoUrl={logo}
            colors={["#cba6f7", "#7a2ee0"]} accentColor="#7a2ee0" menuButtonColor={btn} openMenuButtonColor="#18181b" />
        </div>
      </Example>
      <Example title="Izquierda, sin numeración ni redes">
        <div className="relative h-96 overflow-hidden rounded-xl border border-input bg-muted">
          <StaggeredMenu isFixed={false} position="left" items={items} displaySocials={false} displayItemNumbering={false}
            logoUrl={logo} colors={["#a6e3d6", "#13777d"]} accentColor="#13777d" menuButtonColor={btn} openMenuButtonColor="#18181b" />
        </div>
      </Example>
    </>
  );
}
