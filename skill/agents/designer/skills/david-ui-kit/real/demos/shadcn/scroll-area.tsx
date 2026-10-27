import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Example } from "@kit/demo";

const items = Array.from({ length: 24 }, (_, i) => `Pedido PED-${1300 - i} · ${["Boda", "Cumpleaños", "Corporativo", "Graduación"][i % 4]}`);
const colors = ["Rosa", "Lila", "Menta", "Dorado", "Azul", "Coral", "Blanco", "Negro", "Plata", "Verde", "Rojo", "Naranja"];

export default function ScrollAreaDemo() {
  return (
    <>
      <Example title="Lista vertical">
        <ScrollArea className="h-56 w-72 rounded-lg border border-border">
          <div className="p-3">
            <h4 className="mb-2 text-sm font-medium">Pedidos recientes</h4>
            {items.map((t) => <div key={t} className="border-b border-border py-2 text-sm last:border-0">{t}</div>)}
          </div>
        </ScrollArea>
      </Example>
      <Example title="Horizontal">
        <ScrollArea className="w-full max-w-md rounded-lg border border-border whitespace-nowrap">
          <div className="flex gap-3 p-3">
            {colors.map((c, i) => (
              <div key={c} className="flex w-28 shrink-0 flex-col gap-2">
                <div className="h-20 rounded-md" style={{ background: `hsl(${i * 30} 65% 62%)` }} />
                <span className="text-sm text-muted-foreground">{c}</span>
              </div>
            ))}
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </Example>
    </>
  );
}
