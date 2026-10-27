import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Example } from "@kit/demo";

export default function TabsDemo() {
  return (
    <>
      <Example title="Pestañas de pedido (cambia para ver el indicador)">
        <Tabs defaultValue="resumen" className="max-w-md">
          <TabsList>
            <TabsTrigger value="resumen">Resumen</TabsTrigger>
            <TabsTrigger value="materiales">Materiales</TabsTrigger>
            <TabsTrigger value="entrega">Entrega</TabsTrigger>
            <TabsTrigger value="facturas" disabled>Facturas</TabsTrigger>
          </TabsList>
          <TabsContent value="resumen" className="text-sm">Arco orgánico para la boda Ruiz, 14 de noviembre.</TabsContent>
          <TabsContent value="materiales" className="text-sm">180 globos de látex, 40 de foil y 12 m de guirnalda.</TabsContent>
          <TabsContent value="entrega" className="text-sm">Salón Aurora, montaje desde las 10:00.</TabsContent>
        </Tabs>
      </Example>
      <Example title="Variante línea">
        <Tabs defaultValue="activos" className="max-w-md">
          <TabsList variant="line">
            <TabsTrigger value="activos">Activos</TabsTrigger>
            <TabsTrigger value="entregados">Entregados</TabsTrigger>
            <TabsTrigger value="cancelados">Cancelados</TabsTrigger>
          </TabsList>
          <TabsContent value="activos" className="text-sm">12 pedidos en curso.</TabsContent>
          <TabsContent value="entregados" className="text-sm">148 pedidos entregados este año.</TabsContent>
          <TabsContent value="cancelados" className="text-sm">Sin pedidos cancelados.</TabsContent>
        </Tabs>
      </Example>
      <Example title="Vertical">
        <Tabs defaultValue="datos" orientation="vertical" className="max-w-md">
          <TabsList>
            <TabsTrigger value="datos">Datos</TabsTrigger>
            <TabsTrigger value="pagos">Pagos</TabsTrigger>
          </TabsList>
          <TabsContent value="datos" className="text-sm">Laura Ruiz · laura@ruiz.co</TabsContent>
          <TabsContent value="pagos" className="text-sm">Anticipo del 50 % recibido.</TabsContent>
        </Tabs>
      </Example>
    </>
  );
}
