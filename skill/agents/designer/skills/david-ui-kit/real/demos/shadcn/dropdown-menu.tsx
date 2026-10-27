import * as React from "react";
import { ChevronDown, Copy, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuShortcut, DropdownMenuSub, DropdownMenuSubContent, DropdownMenuSubTrigger, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Example, Row } from "@kit/demo";

export default function DropdownMenuDemo() {
  const [estado, setEstado] = React.useState("produccion");
  const [aviso, setAviso] = React.useState(true);
  return (
    <>
      <Example title="Acciones de pedido" className="min-h-72">
        <Row>
          <DropdownMenu defaultOpen>
            <DropdownMenuTrigger render={<Button variant="outline" />}>Pedido #1042<ChevronDown data-icon="inline-end" /></DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="start">
              <DropdownMenuGroup>
                <DropdownMenuLabel>Acciones</DropdownMenuLabel>
                <DropdownMenuItem><Pencil />Editar<DropdownMenuShortcut>⌘E</DropdownMenuShortcut></DropdownMenuItem>
                <DropdownMenuItem><Copy />Duplicar<DropdownMenuShortcut>⌘D</DropdownMenuShortcut></DropdownMenuItem>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>Mover a salón</DropdownMenuSubTrigger>
                  <DropdownMenuSubContent>
                    <DropdownMenuItem>Salón Aurora</DropdownMenuItem>
                    <DropdownMenuItem>Terraza Norte</DropdownMenuItem>
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem variant="destructive"><Trash2 />Cancelar pedido</DropdownMenuItem>
              <DropdownMenuItem disabled>Facturar (requiere pago)</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </Row>
      </Example>
      <Example title="Casillas y opciones (cierra y vuelve a abrir)">
        <Row>
          <DropdownMenu>
            <DropdownMenuTrigger render={<Button variant="secondary" />}>Estado y avisos</DropdownMenuTrigger>
            <DropdownMenuContent className="w-56">
              <DropdownMenuGroup>
                <DropdownMenuLabel>Estado</DropdownMenuLabel>
                <DropdownMenuRadioGroup value={estado} onValueChange={setEstado}>
                  <DropdownMenuRadioItem value="diseno">Diseño</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="produccion">Producción</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="entregado">Entregado</DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuCheckboxItem checked={aviso} onCheckedChange={setAviso}>Avisar al cliente</DropdownMenuCheckboxItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger render={<Button variant="ghost" size="icon" aria-label="Más acciones" />}><MoreHorizontal /></DropdownMenuTrigger>
            <DropdownMenuContent align="end"><DropdownMenuItem>Ver cliente</DropdownMenuItem><DropdownMenuItem>Imprimir ficha</DropdownMenuItem></DropdownMenuContent>
          </DropdownMenu>
        </Row>
      </Example>
    </>
  );
}
