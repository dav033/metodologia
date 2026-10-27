import { CalendarDays, Home, Package, Settings, Users } from "lucide-react";
import { Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupLabel, SidebarHeader, SidebarInset, SidebarMenu, SidebarMenuBadge, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Example } from "@kit/demo";

const items = [
  { label: "Inicio", icon: Home, active: true },
  { label: "Pedidos", icon: Package, badge: "12" },
  { label: "Clientes", icon: Users },
  { label: "Eventos", icon: CalendarDays, badge: "3" },
];

function Shell({ collapsible }: { collapsible: "none" | "icon" }) {
  return (
    <div className="relative h-80 overflow-hidden rounded-xl border [transform:translateZ(0)]">
      <SidebarProvider className="h-full min-h-0" style={{ "--sidebar-width": "13rem" } as React.CSSProperties}>
        <Sidebar collapsible={collapsible} className={collapsible === "icon" ? "absolute! h-full! [&_[data-slot=sidebar-container]]:absolute! [&_[data-slot=sidebar-container]]:h-full!" : undefined}>
          <SidebarHeader className="px-3 py-3 text-sm font-semibold">Globos & Eventos</SidebarHeader>
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Operación</SidebarGroupLabel>
              <SidebarMenu>
                {items.map((it) => (
                  <SidebarMenuItem key={it.label}>
                    <SidebarMenuButton isActive={it.active} tooltip={it.label}>
                      <it.icon /><span>{it.label}</span>
                    </SidebarMenuButton>
                    {it.badge && <SidebarMenuBadge>{it.badge}</SidebarMenuBadge>}
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroup>
          </SidebarContent>
          <SidebarFooter>
            <SidebarMenu><SidebarMenuItem><SidebarMenuButton><Settings /><span>Ajustes</span></SidebarMenuButton></SidebarMenuItem></SidebarMenu>
          </SidebarFooter>
        </Sidebar>
        <SidebarInset className="min-h-0 overflow-auto">
          <header className="flex h-12 items-center gap-2 border-b px-3">
            <SidebarTrigger aria-label="Alternar barra lateral" />
            <span className="text-sm font-medium">Panel de pedidos</span>
          </header>
          <div className="p-4 text-sm text-muted-foreground">Hoy hay 12 pedidos activos y 3 eventos esta semana.</div>
        </SidebarInset>
      </SidebarProvider>
    </div>
  );
}

export default function SidebarDemo() {
  return (
    <>
      <Example title="Barra fija con insignias">
        <Shell collapsible="none" />
      </Example>
      <Example title="Colapsable a iconos (usa el botón del encabezado)">
        <Shell collapsible="icon" />
      </Example>
    </>
  );
}
