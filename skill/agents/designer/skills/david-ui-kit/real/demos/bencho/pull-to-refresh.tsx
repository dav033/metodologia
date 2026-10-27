import { Balance } from "@/components/bencho/pull/Balance";
import "@/components/bencho/pull/Balance.css";
import { Example } from "@kit/demo";

export default function PullToRefreshDemo() {
  return (
    <>
      <Example title="Arrastrar la tarjeta hacia abajo para actualizar (teclado: Enter sobre la tarjeta)">
        <div className="bencho flex justify-center p-6"><Balance /></div>
      </Example>
      <Example title="Más marcas en la rueda de carga">
        <div className="bencho flex justify-center p-6"><Balance dots={9} spin={80} /></div>
      </Example>
    </>
  );
}
