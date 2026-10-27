// Reference mockup: sign-in, account activation and password reset on one centred axis (brand, card, footnote),
// everything inside the card left-aligned. Built only from installed shadcn/ui components + Motion.
import { motion } from "motion/react";
import { AlertCircle, Loader2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { mountMockup, useMockup } from "@kit/mockup";
import { useReveal } from "@kit/motion";

const COPY = {
  login: { title: "Iniciar sesión", lede: "Usa el correo con el que te invitaron.", cta: "Entrar" },
  activar: { title: "Activa tu cuenta", lede: "Elige una contraseña para empezar a planear eventos.", cta: "Activar cuenta" },
  restablecer: { title: "Restablecer contraseña", lede: "Te enviaremos un enlace a tu correo.", cta: "Enviar enlace" },
} as const;

function Rise({ i, children }: { i: number; children: React.ReactNode }) {
  const reveal = useReveal();
  return (
    <motion.div {...reveal(i)}>
      {children}
    </motion.div>
  );
}

function Screen() {
  const { view, state } = useMockup();
  const v = (COPY as Record<string, (typeof COPY)["login"]>)[view] ?? COPY.login;
  const loading = state === "cargando";
  const error = state === "error";
  return (
    <div className="flex min-h-[calc(100svh-var(--mockup-bar-h))] items-center justify-center bg-background px-4 py-10">
      <div className="flex w-full max-w-sm flex-col items-center gap-6">
        <Rise i={0}>
          <div className="flex items-center gap-2 text-foreground">
            <span className="grid size-9 place-items-center rounded-xl bg-primary font-semibold text-primary-foreground">P</span>
            <span className="text-lg font-semibold tracking-tight">Pictures</span>
          </div>
        </Rise>
        <Rise i={1}>
          <Card className="w-[min(24rem,calc(100vw-2rem))]">
            <CardHeader>
              <CardTitle className="text-xl">{v.title}</CardTitle>
              <CardDescription>{v.lede}</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="flex flex-col gap-5" onSubmit={(e) => e.preventDefault()}>
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle />
                    <AlertTitle>No pudimos {view === "restablecer" ? "enviar el enlace" : "entrar"}</AlertTitle>
                    <AlertDescription>Revisa el correo y la contraseña e inténtalo de nuevo.</AlertDescription>
                  </Alert>
                )}
                <FieldGroup>
                  <Field data-invalid={error || undefined}>
                    <FieldLabel htmlFor="email">Correo</FieldLabel>
                    <Input id="email" type="email" defaultValue="ana@decoraciones.co" aria-invalid={error || undefined} disabled={loading} />
                  </Field>
                  {view !== "restablecer" && (
                    <Field data-invalid={error || undefined}>
                      <div className="flex items-center justify-between gap-3">
                        <FieldLabel htmlFor="pw">{view === "activar" ? "Nueva contraseña" : "Contraseña"}</FieldLabel>
                        {view === "login" && <a href="#restablecer" className="text-sm font-medium text-primary underline-offset-4 hover:underline">¿Olvidaste tu contraseña?</a>}
                      </div>
                      <Input id="pw" type="password" defaultValue="globos-2026" aria-invalid={error || undefined} disabled={loading} />
                      {view === "activar" && <FieldDescription>Mínimo 12 caracteres.</FieldDescription>}
                      {error && <FieldError>Correo o contraseña incorrectos.</FieldError>}
                    </Field>
                  )}
                </FieldGroup>
                <Button type="submit" size="lg" className="w-full" disabled={loading}>
                  {loading && <Loader2 className="animate-spin" data-icon="inline-start" />}
                  {loading ? "Un momento…" : v.cta}
                </Button>
              </form>
            </CardContent>
            {view !== "login" && (
              <CardFooter>
                <Button variant="ghost" className="w-full">Volver a iniciar sesión</Button>
              </CardFooter>
            )}
          </Card>
        </Rise>
        <Rise i={2}>
          <p className="text-center text-sm text-muted-foreground">¿Problemas para entrar? Escribe a soporte@decoraciones.co</p>
        </Rise>
      </div>
    </div>
  );
}

mountMockup(Screen, {
  title: "Acceso",
  views: [{ id: "login", label: "Iniciar sesión" }, { id: "activar", label: "Activar cuenta" }, { id: "restablecer", label: "Restablecer contraseña" }],
  states: [{ id: "normal", label: "Normal" }, { id: "cargando", label: "Cargando" }, { id: "error", label: "Error" }],
});
