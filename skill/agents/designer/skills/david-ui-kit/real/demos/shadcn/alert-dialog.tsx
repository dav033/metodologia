import { Trash2 } from "lucide-react";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogMedia, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Example } from "@kit/demo";

export default function AlertDialogDemo() {
  return (
    <>
      <Example title="Cancelar pedido (abierto; ciérralo y vuelve a abrirlo)" className="min-h-80">
        <AlertDialog defaultOpen>
          <AlertDialogTrigger render={<Button variant="destructive" />}>Cancelar pedido</AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogMedia><Trash2 /></AlertDialogMedia>
              <AlertDialogTitle>¿Cancelar el pedido #1042?</AlertDialogTitle>
              <AlertDialogDescription>Se liberarán los 180 globos reservados y se avisará a Laura Ruiz. Esta acción no se puede deshacer.</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Mantener pedido</AlertDialogCancel>
              <AlertDialogAction variant="destructive">Sí, cancelar</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </Example>
      <Example title="Confirmación simple, tamaño pequeño">
        <AlertDialog>
          <AlertDialogTrigger render={<Button variant="outline" />}>Archivar evento</AlertDialogTrigger>
          <AlertDialogContent size="sm">
            <AlertDialogHeader>
              <AlertDialogTitle>¿Archivar el evento?</AlertDialogTitle>
              <AlertDialogDescription>Podrás recuperarlo desde Archivados.</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Volver</AlertDialogCancel>
              <AlertDialogAction>Archivar</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </Example>
    </>
  );
}
