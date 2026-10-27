import Shuffle from "@/components/react-bits/Shuffle";
import { Example } from "@kit/demo";
import { useMotionProfile } from "@kit/motion";

export default function ShuffleDemo() {
  const { reduced } = useMotionProfile();
  return (
    <>
      <Example title="Titular que se reordena al entrar">
        <Shuffle text="FIESTA" tag="h2" shuffleDirection="right" duration={0.45} animationMode="evenodd"
          className="text-5xl font-bold" colorFrom="var(--primary)" colorTo="var(--foreground)" textAlign="left" />
      </Example>
      <Example title="Efecto de volteo, con bucle">
        <Shuffle text="Globos de látex" tag="p" effect="flip" shuffleDirection="up" loop={!reduced} loopDelay={2}
          className="text-3xl font-semibold" textAlign="left" />
      </Example>
      <Example title="Solo al pasar el cursor">
        <Shuffle text="Pasa el cursor aquí" tag="p" triggerOnHover effect="blur" className="text-xl" textAlign="left" />
      </Example>
    </>
  );
}
