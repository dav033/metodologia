import { ScrollFade } from "@animate-ui/react/primitives/effects/scroll-fade";
import { Example } from "@kit/demo";

const pedidos = ["Arco orgánico — Salón Aurora", "Centros de mesa — Boda Gómez", "Globos metalizados — Baby shower", "Columnas de globos — Aniversario", "Letras gigantes — XV años", "Piñata de globos — Cumpleaños", "Cortina de globos — Graduación", "Bouquet de globos — Entrega a domicilio"];

export default function ScrollFadeDemo() {
  return (
    <>
      <Example title="Lista vertical con bordes que se desvanecen al hacer scroll">
        <ScrollFade className="h-48 max-w-sm overflow-y-auto rounded-xl border border-input bg-card p-3 text-card-foreground" size={40}>
          <ul className="flex flex-col gap-2">
            {pedidos.map((p) => <li key={p} className="rounded-lg bg-muted px-3 py-2 text-sm text-foreground">{p}</li>)}
          </ul>
        </ScrollFade>
      </Example>
      <Example title="Horizontal">
        <ScrollFade orientation="horizontal" className="flex max-w-sm gap-2 overflow-x-auto rounded-xl border border-input bg-card p-3">
          {pedidos.map((p) => <span key={p} className="shrink-0 whitespace-nowrap rounded-full bg-secondary px-3 py-1 text-sm text-secondary-foreground">{p.split(" — ")[0]}</span>)}
        </ScrollFade>
      </Example>
    </>
  );
}
