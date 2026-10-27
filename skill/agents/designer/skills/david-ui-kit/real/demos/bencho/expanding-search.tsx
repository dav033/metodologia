import { Seek } from "@/components/bencho/seek/Seek";
import "@/components/bencho/seek/Seek.css";
import { Example } from "@kit/demo";

export default function ExpandingSearchDemo() {
  return (
    <>
      <Example title="Pulsar la lupa para abrir el campo">
        <div className="bencho flex justify-center p-6"><Seek /></div>
      </Example>
      <Example title="Campo ancho con mucha holgura">
        <div className="bencho flex justify-center p-6"><Seek width={380} give={80} /></div>
      </Example>
    </>
  );
}
