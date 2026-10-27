import AnimatedContent from "@/components/react-bits/AnimatedContent";
import { Example } from "@kit/demo";

const cards = ["Cotización enviada", "Anticipo recibido", "Montaje programado"];

export default function AnimatedContentDemo() {
  return (
    <>
      <Example title="Entrada escalonada al montarse">
        <AnimatedContent trigger="mount" distance={40} stagger={0.12} duration={0.8} className="grid gap-3 sm:grid-cols-3">
          {cards.map((c) => (
            <div key={c} className="rounded-xl border border-input bg-card p-4 text-card-foreground">
              <p className="font-medium">{c}</p>
              <p className="mt-1 text-sm text-muted-foreground">Pedido #2048</p>
            </div>
          ))}
        </AnimatedContent>
      </Example>
      <Example title="Con desenfoque y escala, horizontal inverso">
        <AnimatedContent trigger="mount" direction="horizontal" reverse blur={8} scale={0.9} duration={0.9}>
          <div className="rounded-xl bg-primary p-5 text-primary-foreground">
            <p className="text-lg font-semibold">Evento confirmado</p>
            <p className="text-sm">Salón Aurora · 14 de noviembre</p>
          </div>
        </AnimatedContent>
      </Example>
    </>
  );
}
