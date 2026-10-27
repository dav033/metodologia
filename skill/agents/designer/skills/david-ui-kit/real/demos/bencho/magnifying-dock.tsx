import { GlassDock } from "@/components/bencho/dock/GlassDock";
import "@/components/bencho/dock/GlassDock.css";
import { Example } from "@kit/demo";

export default function MagnifyingDockDemo() {
  return (
    <>
      <Example title="Dock que crece hacia el cursor">
        <div className="bencho flex justify-center p-6"><GlassDock /></div>
      </Example>
      <Example title="Magnificación fuerte y alcance amplio">
        <div className="bencho flex justify-center p-6"><GlassDock magnify={1.7} spread={3} lift={14} /></div>
      </Example>
    </>
  );
}
