import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Example } from "@kit/demo";

export default function DialogDemo() {
  return (
    <>
      <Example title="Editar cliente (abierto; ciérralo y vuelve a abrirlo para ver la animación)" className="min-h-80">
        <Dialog defaultOpen>
          <DialogTrigger render={<Button />}>Editar cliente</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Editar cliente</DialogTitle>
              <DialogDescription>Actualiza los datos de contacto de Laura Ruiz.</DialogDescription>
            </DialogHeader>
            <Field>
              <FieldLabel htmlFor="d-tel">Teléfono</FieldLabel>
              <Input id="d-tel" defaultValue="+57 300 123 4567" />
            </Field>
            <DialogFooter>
              <DialogClose render={<Button variant="outline" />}>Cancelar</DialogClose>
              <DialogClose render={<Button />}>Guardar</DialogClose>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </Example>
      <Example title="Sin botón de cierre">
        <Dialog>
          <DialogTrigger render={<Button variant="outline" />}>Ver aviso</DialogTrigger>
          <DialogContent showCloseButton={false}>
            <DialogHeader>
              <DialogTitle>Entrega confirmada</DialogTitle>
              <DialogDescription>El Salón Aurora recibió el arco a las 13:40.</DialogDescription>
            </DialogHeader>
            <DialogFooter><DialogClose render={<Button />}>Entendido</DialogClose></DialogFooter>
          </DialogContent>
        </Dialog>
      </Example>
    </>
  );
}
