import * as React from "react";
import { CalendarIcon } from "lucide-react";
import { es } from "react-day-picker/locale";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Example } from "@kit/demo";

function DatePicker({ initial, disabled, defaultOpen }: { initial?: Date; disabled?: boolean; defaultOpen?: boolean }) {
  const [date, setDate] = React.useState<Date | undefined>(initial);
  const [open, setOpen] = React.useState(!!defaultOpen);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger render={<Button variant="outline" disabled={disabled} className="w-60 justify-start font-normal" />}>
        <CalendarIcon data-icon="inline-start" />
        {date ? date.toLocaleDateString("es-CO", { dateStyle: "long" }) : <span className="text-muted-foreground">Elige la fecha del evento</span>}
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar mode="single" locale={es} defaultMonth={date ?? new Date(2026, 10)} selected={date} onSelect={(d) => { setDate(d); if (d) setOpen(false); }} />
      </PopoverContent>
    </Popover>
  );
}

export default function DatePickerDemo() {
  return (
    <>
      <Example title="Abierto (elige una fecha para cerrarlo)">
        <div className="min-h-96"><DatePicker defaultOpen /></div>
      </Example>
      <Example title="Con valor y deshabilitado">
        <div className="flex flex-wrap gap-3">
          <DatePicker initial={new Date(2026, 11, 5)} />
          <DatePicker disabled />
        </div>
      </Example>
    </>
  );
}
