// Reference mockup: an admin list screen (sidebar, header with the page action on the right, filters, data table with a
// row menu, empty/loading/error states and a destructive confirmation). Real shadcn/ui on Base UI + Animate UI motion.
import { motion } from "motion/react";
import { AlertCircle, CalendarDays, Home, MoreHorizontal, Plus, Search, Settings, Users } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { InputGroup, InputGroupAddon, InputGroupInput } from "@/components/ui/input-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarHeader, SidebarInset, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { mountMockup, useMockup } from "@kit/mockup";
import { useReveal } from "@kit/motion";

const PEOPLE = [
  { name: "Ana Restrepo", email: "ana@decoraciones.co", company: "Decoraciones Ana", role: "Administradora", status: "activa" },
  { name: "Julián Mora", email: "julian@fiestasmora.co", company: "Fiestas Mora", role: "Decorador", status: "invitada" },
  { name: "Camila Ortiz", email: "camila@globoarte.co", company: "GloboArte", role: "Decoradora", status: "activa" },
  { name: "Pedro Salas", email: "pedro@eventosps.co", company: "Eventos PS", role: "Asesor", status: "suspendida" },
  { name: "Lucía Gómez", email: "lucia@lucydeco.co", company: "Lucy Deco", role: "Decoradora", status: "activa" },
];
const STATUS: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  activa: { label: "Activa", variant: "secondary" }, invitada: { label: "Invitada", variant: "outline" },
  suspendida: { label: "Suspendida", variant: "destructive" },
};
const NAV = [{ icon: Home, label: "Inicio" }, { icon: CalendarDays, label: "Eventos" }, { icon: Users, label: "Cuentas", active: true }, { icon: Settings, label: "Ajustes" }];

function Rows() {
  const { state, set } = useMockup();
  const reveal = useReveal();
  if (state === "cargando") {
    return <>{[0, 1, 2, 3].map((i) => (
      <TableRow key={i}><TableCell colSpan={5}><div className="flex items-center gap-3"><Skeleton className="size-8 rounded-full" /><Skeleton className="h-4 w-48" /><Skeleton className="ml-auto h-4 w-24" /></div></TableCell></TableRow>
    ))}</>;
  }
  return <>{PEOPLE.map((p, i) => (
    <motion.tr key={p.email} data-slot="table-row" className="border-b transition-colors hover:bg-muted/50"
      {...reveal(i)}>
      <TableCell>
        <div className="flex items-center gap-3">
          <Avatar className="size-8"><AvatarFallback>{p.name.split(" ").map((w) => w[0]).join("")}</AvatarFallback></Avatar>
          <div className="flex min-w-0 flex-col"><span className="font-medium">{p.name}</span><span className="truncate text-muted-foreground">{p.email}</span></div>
        </div>
      </TableCell>
      <TableCell className="hidden md:table-cell">{p.company}</TableCell>
      <TableCell className="hidden lg:table-cell">{p.role}</TableCell>
      <TableCell><Badge variant={STATUS[p.status].variant}>{STATUS[p.status].label}</Badge></TableCell>
      <TableCell className="text-right">
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="ghost" size="icon" aria-label={`Acciones de ${p.name}`} />}><MoreHorizontal /></DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Ver cuenta</DropdownMenuItem>
            <DropdownMenuItem>Cambiar rol</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onClick={() => set("scene", "eliminar")}>Eliminar cuenta</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </motion.tr>
  ))}</>;
}

function Screen() {
  const { state, scene, set } = useMockup();
  return (
    <SidebarProvider className="min-h-[calc(100svh-var(--mockup-bar-h))]">
      <Sidebar collapsible="offcanvas">
        <SidebarHeader><div className="flex items-center gap-2 px-2 py-1.5"><span className="grid size-8 place-items-center rounded-lg bg-primary font-semibold text-primary-foreground">P</span><span className="font-semibold">Pictures</span></div></SidebarHeader>
        <SidebarContent><SidebarGroup><SidebarGroupContent><SidebarMenu>
          {NAV.map(({ icon: Icon, label, active }) => (
            <SidebarMenuItem key={label}><SidebarMenuButton isActive={active}><Icon />{label}</SidebarMenuButton></SidebarMenuItem>
          ))}
        </SidebarMenu></SidebarGroupContent></SidebarGroup></SidebarContent>
      </Sidebar>
      <SidebarInset>
        <header className="flex h-14 items-center gap-2 border-b px-4"><SidebarTrigger /><span className="text-sm text-muted-foreground">Administración</span></header>
        <main className="flex flex-col gap-6 p-4 md:p-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="flex flex-col gap-1"><h1 className="text-2xl font-semibold tracking-tight">Cuentas</h1><p className="text-sm text-muted-foreground">Personas con acceso al planeador de decoración.</p></div>
            <Button><Plus data-icon="inline-start" />Invitar persona</Button>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <InputGroup className="w-full sm:w-72"><InputGroupAddon><Search /></InputGroupAddon><InputGroupInput placeholder="Buscar por nombre o correo" aria-label="Buscar cuentas" /></InputGroup>
            <Select items={[{ value: "todos", label: "Todos los estados" }, { value: "activa", label: "Activas" }, { value: "invitada", label: "Invitadas" }, { value: "suspendida", label: "Suspendidas" }]} defaultValue="todos">
              <SelectTrigger className="w-44" aria-label="Filtrar por estado"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="todos">Todos los estados</SelectItem><SelectItem value="activa">Activas</SelectItem><SelectItem value="invitada">Invitadas</SelectItem><SelectItem value="suspendida">Suspendidas</SelectItem></SelectContent>
            </Select>
          </div>
          {state === "error" && (
            <Alert variant="destructive"><AlertCircle /><AlertTitle>No pudimos cargar las cuentas</AlertTitle><AlertDescription>Reintenta en unos segundos.</AlertDescription></Alert>
          )}
          {state === "vacio" ? (
            <Empty className="border">
              <EmptyHeader><EmptyMedia variant="icon"><Users /></EmptyMedia><EmptyTitle>Todavía no hay cuentas</EmptyTitle><EmptyDescription>Invita a tu equipo para que empiece a planear eventos.</EmptyDescription></EmptyHeader>
              <EmptyContent><Button><Plus data-icon="inline-start" />Invitar persona</Button></EmptyContent>
            </Empty>
          ) : state !== "error" && (
            <div className="overflow-x-auto rounded-xl border bg-card">
              <Table>
                <TableHeader><TableRow><TableHead>Persona</TableHead><TableHead className="hidden md:table-cell">Empresa</TableHead><TableHead className="hidden lg:table-cell">Rol</TableHead><TableHead>Estado</TableHead><TableHead className="text-right">Acciones</TableHead></TableRow></TableHeader>
                <TableBody><Rows /></TableBody>
              </Table>
            </div>
          )}
        </main>
      </SidebarInset>
      <AlertDialog open={scene === "eliminar"} onOpenChange={(o) => !o && set("scene", "")}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>¿Eliminar la cuenta de Pedro Salas?</AlertDialogTitle><AlertDialogDescription>Perderá el acceso de inmediato. Sus eventos quedan en la empresa.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>Cancelar</AlertDialogCancel><AlertDialogAction variant="destructive">Eliminar cuenta</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </SidebarProvider>
  );
}

mountMockup(Screen, {
  title: "Cuentas",
  views: [{ id: "lista", label: "Lista de cuentas" }],
  states: [{ id: "normal", label: "Con datos" }, { id: "cargando", label: "Cargando" }, { id: "vacio", label: "Vacío" }, { id: "error", label: "Error" }],
  scenes: [{ id: "", label: "Ninguno" }, { id: "eliminar", label: "Eliminar cuenta" }],
});
