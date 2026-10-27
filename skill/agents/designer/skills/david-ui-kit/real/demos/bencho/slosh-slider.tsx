import { Slosh } from "@/components/bencho/slosh/Slosh";
import "@/components/bencho/slosh/Slosh.css";
import { Example } from "@kit/demo";

export default function SloshSliderDemo() {
  return (
    <>
      <Example title="Deslizador con fluido: arrastrar rápido (teclado: flechas con foco)">
        <div className="bencho flex justify-center p-6"><Slosh /></div>
      </Example>
      <Example title="Fluido suelto">
        <div className="bencho flex justify-center p-6"><Slosh viscosity={70} momentum={80} /></div>
      </Example>
    </>
  );
}
