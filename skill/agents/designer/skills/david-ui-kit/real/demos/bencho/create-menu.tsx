import { Create } from "@/components/bencho/liq-create/Create";
import "@/components/bencho/liq-create/Create.css";
import { Example } from "@kit/demo";

export default function CreateMenuDemo() {
  return (
    <>
      <Example title="Pulsar el botón para abrir el menú de creación">
        <div className="bencho flex justify-center p-6"><Create /></div>
      </Example>
      <Example title="Esquina reducida">
        <div className="bencho flex justify-center p-6"><Create corner={10} /></div>
      </Example>
    </>
  );
}
