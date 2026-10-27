import { Link as LinkIcon } from "lucide-react";
import { NavigationMenu, NavigationMenuContent, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuPositioner, NavigationMenuTrigger } from "@/components/ui/navigation-menu";
import { Example } from "@kit/demo";

const catalog = [
  { t: "Arcos orgánicos", d: "Guirnaldas de globos en varios tamaños." },
  { t: "Globos foil", d: "Letras, números y figuras metalizadas." },
  { t: "Centros de mesa", d: "Composiciones para banquetes y bodas." },
];

export default function NavigationMenuDemo() {
  return (
    <>
      <Example title="Menú con paneles (el panel cambia de tamaño con animación)">
        <div className="min-h-72">
          <NavigationMenu defaultValue="catalogo">
            <NavigationMenuList>
              <NavigationMenuItem value="catalogo">
                <NavigationMenuTrigger>Catálogo</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid w-80 gap-1">
                    {catalog.map((c) => (
                      <li key={c.t}>
                        <NavigationMenuLink href="#catalogo" className="flex flex-col gap-0.5">
                          <span className="font-medium">{c.t}</span>
                          <span className="text-xs text-muted-foreground">{c.d}</span>
                        </NavigationMenuLink>
                      </li>
                    ))}
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>
              <NavigationMenuItem value="eventos">
                <NavigationMenuTrigger>Eventos</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid w-56 gap-1">
                    {["Bodas", "Corporativos", "Cumpleaños"].map((e) => (
                      <li key={e}><NavigationMenuLink href="#eventos">{e}</NavigationMenuLink></li>
                    ))}
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuLink href="#contacto">Contacto</NavigationMenuLink>
              </NavigationMenuItem>
            </NavigationMenuList>
            <NavigationMenuPositioner />
          </NavigationMenu>
        </div>
      </Example>
      <Example title="Solo enlaces">
        <NavigationMenu>
          <NavigationMenuList>
            {["Inicio", "Pedidos", "Clientes"].map((l) => (
              <NavigationMenuItem key={l}><NavigationMenuLink href={`#${l}`}>{l}</NavigationMenuLink></NavigationMenuItem>
            ))}
            <NavigationMenuItem><NavigationMenuLink href="#externo"><LinkIcon className="size-3.5" />Tienda en línea</NavigationMenuLink></NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
      </Example>
    </>
  );
}
