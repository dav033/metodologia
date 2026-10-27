// Reference mockup: a form page with validation, a confirmation dialog and a result toast. Real shadcn/ui (Base UI +
// Animate UI dialog motion) and Sonner; scenes open the dialog and show the toast so the plan page can drive them.
import * as React from "react";
import { motion } from "motion/react";
import { toast } from "sonner";
import { ArrowLeft, Loader2, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Toaster } from "@/components/ui/sonner";
import { mountMockup, useMockup } from "@kit/mockup";
import { useReveal } from "@kit/motion";

const ROLES = [
  { id: "decorador", label: "Decorador", hint: "Planea eventos y arma propuestas." },
  { id: "asesor", label: "Asesor", hint: "Acompaña pedidos de clientes de la empresa." },
  { id: "admin", label: "Administrador", hint: "Gestiona cuentas, roles y facturación." },
];

function Screen() {
  const { state, scene, theme, set } = useMockup();
  const reveal = useReveal();
  const error = state === "error";
  const sending = state === "enviando";
  React.useEffect(() => {
    if (scene !== "enviado") return;
    const id = toast.success("Invitación enviada a julian@fiestasmora.co", { description: "Le llegará un enlace válido por 7 días.", duration: Infinity });
    return () => { toast.dismiss(id); };
  }, [scene]);
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 px-4 py-8 md:py-12">
      <motion.div {...reveal(0)} className="flex flex-col gap-3">
        <Button variant="ghost" size="sm" className="w-fit"><ArrowLeft data-icon="inline-start" />Cuentas</Button>
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">Invitar persona</h1>
          <p className="text-sm text-muted-foreground">Le enviaremos un correo para que active su cuenta.</p>
        </div>
      </motion.div>
      <motion.div {...reveal(1)}>
        <Card>
          <CardHeader>
            <CardTitle>Datos de la invitación</CardTitle>
            <CardDescription>Todos los campos son obligatorios salvo el mensaje.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-6" onSubmit={(e) => { e.preventDefault(); set("scene", "confirmar"); }}>
              <FieldGroup>
                <div className="grid gap-6 sm:grid-cols-2">
                  <Field><FieldLabel htmlFor="nombre">Nombre</FieldLabel><Input id="nombre" defaultValue="Julián Mora" disabled={sending} /></Field>
                  <Field data-invalid={error || undefined}>
                    <FieldLabel htmlFor="correo">Correo</FieldLabel>
                    <Input id="correo" type="email" defaultValue={error ? "julian@fiestasmora" : "julian@fiestasmora.co"} aria-invalid={error || undefined} disabled={sending} />
                    {error && <FieldError>Escribe un correo completo, por ejemplo nombre@empresa.co.</FieldError>}
                  </Field>
                </div>
                <Field>
                  <FieldLabel>Rol</FieldLabel>
                  <RadioGroup defaultValue="decorador" className="gap-3" disabled={sending}>
                    {ROLES.map((r) => (
                      <Label key={r.id} htmlFor={`rol-${r.id}`} className="flex items-start gap-3 rounded-lg border p-4 has-data-checked:border-primary has-data-checked:bg-primary-soft">
                        <RadioGroupItem id={`rol-${r.id}`} value={r.id} className="mt-0.5" />
                        <span className="flex flex-col gap-1"><span className="font-medium">{r.label}</span><span className="text-sm font-normal text-muted-foreground">{r.hint}</span></span>
                      </Label>
                    ))}
                  </RadioGroup>
                </Field>
                <Field>
                  <FieldLabel htmlFor="mensaje">Mensaje (opcional)</FieldLabel>
                  <Textarea id="mensaje" rows={3} defaultValue="¡Hola Julián! Te sumo al equipo para la temporada de bodas." disabled={sending} />
                  <FieldDescription>Aparece al comienzo del correo.</FieldDescription>
                </Field>
              </FieldGroup>
            </form>
          </CardContent>
          <CardFooter className="justify-end gap-3 border-t">
            <Button variant="outline" disabled={sending}>Cancelar</Button>
            <Button onClick={() => set("scene", "confirmar")} disabled={sending}>
              {sending ? <Loader2 className="animate-spin" data-icon="inline-start" /> : <Send data-icon="inline-start" />}
              {sending ? "Enviando…" : "Enviar invitación"}
            </Button>
          </CardFooter>
        </Card>
      </motion.div>
      <Dialog open={scene === "confirmar"} onOpenChange={(o) => !o && set("scene", "")}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Enviar la invitación a Julián Mora?</DialogTitle>
            <DialogDescription>Recibirá el correo en julian@fiestasmora.co con el rol Decorador.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => set("scene", "")}>Revisar</Button>
            <Button onClick={() => set("scene", "enviado")}>Enviar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Toaster theme={theme} position="bottom-right" />
    </div>
  );
}

mountMockup(Screen, {
  title: "Invitar persona",
  views: [{ id: "formulario", label: "Formulario" }],
  states: [{ id: "normal", label: "Normal" }, { id: "error", label: "Correo inválido" }, { id: "enviando", label: "Enviando" }],
  scenes: [{ id: "", label: "Ninguno" }, { id: "confirmar", label: "Confirmar envío" }, { id: "enviado", label: "Invitación enviada" }],
});
