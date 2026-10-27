import * as React from "react";
import { Calendar, Package, Plus, Search, Settings, Users } from "lucide-react";
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut } from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Example } from "@kit/demo";

function Items() {
  return (
    <>
      <CommandEmpty>Sin resultados.</CommandEmpty>
      <CommandGroup heading="Acciones">
        <CommandItem><Plus />Nuevo pedido<CommandShortcut>⌘N</CommandShortcut></CommandItem>
        <CommandItem><Calendar />Ver calendario de eventos<CommandShortcut>⌘K</CommandShortcut></CommandItem>
      </CommandGroup>
      <CommandSeparator />
      <CommandGroup heading="Ir a">
        <CommandItem><Package />Inventario de globos</CommandItem>
        <CommandItem><Users />Clientes</CommandItem>
        <CommandItem><Settings />Ajustes<CommandShortcut>⌘,</CommandShortcut></CommandItem>
      </CommandGroup>
    </>
  );
}

export default function CommandDemo() {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <Example title="Paleta en línea (escribe para filtrar)">
        <Command className="max-w-md rounded-lg border border-border">
          <CommandInput placeholder="Buscar acción o sección…" />
          <CommandList><Items /></CommandList>
        </Command>
      </Example>
      <Example title="Sin coincidencias">
        <Command className="max-w-md rounded-lg border border-border">
          <CommandInput placeholder="Buscar…" defaultValue="zzz" />
          <CommandList><Items /></CommandList>
        </Command>
      </Example>
      <Example title="En diálogo">
        <Button variant="outline" onClick={() => setOpen(true)}><Search data-icon="inline-start" />Abrir paleta de comandos</Button>
        <CommandDialog open={open} onOpenChange={setOpen}>
          <Command>
            <CommandInput placeholder="Buscar acción o sección…" />
            <CommandList><Items /></CommandList>
          </Command>
        </CommandDialog>
      </Example>
    </>
  );
}
