import BlurText from "@/components/react-bits/BlurText";
import { Example } from "@kit/demo";
import { useMotionProfile } from "@kit/motion";

export default function BlurTextDemo() {
  const { reduced, stagger } = useMotionProfile();
  const delay = Math.round(stagger * 2000);
  return (
    <>
      <Example title="Titular por palabras (al entrar en pantalla)">
        <BlurText text="Decoramos cada salón con globos que se recuerdan" delay={delay} animateBy="words" direction="top"
          className="text-3xl font-semibold leading-tight" />
      </Example>
      <Example title="Por letras, desde el centro, con color de acento">
        <BlurText text="Evento confirmado" animateBy="letters" effect="focus" staggerFrom="center" delay={40}
          color="var(--primary)" className="text-4xl font-bold" />
      </Example>
      <Example title="Al pasar el cursor (repetible)">
        <BlurText text="Pasa el cursor para ver el pedido" trigger="hover" effect="zoom" loop={!reduced} loopDelay={2500}
          className="text-xl text-muted-foreground" />
      </Example>
    </>
  );
}
