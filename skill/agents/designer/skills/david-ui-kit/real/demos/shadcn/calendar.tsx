import * as React from "react";
import { es } from "react-day-picker/locale";
import type { DateRange } from "react-day-picker";
import { Calendar } from "@/components/ui/calendar";
import { Example } from "@kit/demo";

export default function CalendarDemo() {
  const [date, setDate] = React.useState<Date | undefined>(new Date(2026, 10, 14));
  const [range, setRange] = React.useState<DateRange | undefined>({ from: new Date(2026, 10, 20), to: new Date(2026, 10, 24) });
  return (
    <>
      <Example title="Fecha única">
        <div className="flex flex-wrap items-start gap-4">
          <Calendar mode="single" locale={es} defaultMonth={new Date(2026, 10)} selected={date} onSelect={setDate} className="rounded-lg border border-border" />
          <p className="text-sm text-muted-foreground">Evento: {date ? date.toLocaleDateString("es-CO", { dateStyle: "full" }) : "sin fecha"}</p>
        </div>
      </Example>
      <Example title="Rango con días no disponibles">
        <Calendar
          mode="range" locale={es} numberOfMonths={2} defaultMonth={new Date(2026, 10)}
          selected={range} onSelect={setRange}
          disabled={[{ before: new Date(2026, 10, 3) }, new Date(2026, 10, 14), new Date(2026, 10, 15)]}
          className="rounded-lg border border-border"
        />
      </Example>
    </>
  );
}
