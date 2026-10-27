import { Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart, XAxis } from "recharts";
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";
import { Example } from "@kit/demo";

const months = [
  { mes: "Mayo", bodas: 18, corporativos: 9, cumpleanos: 31 },
  { mes: "Junio", bodas: 24, corporativos: 12, cumpleanos: 28 },
  { mes: "Julio", bodas: 21, corporativos: 15, cumpleanos: 35 },
  { mes: "Agosto", bodas: 30, corporativos: 11, cumpleanos: 33 },
  { mes: "Septiembre", bodas: 27, corporativos: 17, cumpleanos: 40 },
  { mes: "Octubre", bodas: 36, corporativos: 20, cumpleanos: 38 },
];
const config = {
  bodas: { label: "Bodas", color: "var(--chart-1)" },
  corporativos: { label: "Corporativos", color: "var(--chart-2)" },
  cumpleanos: { label: "Cumpleaños", color: "var(--chart-3)" },
} satisfies ChartConfig;

const sales = [
  { globo: "Látex", ventas: 5200, fill: "var(--color-latex)" },
  { globo: "Foil", ventas: 3100, fill: "var(--color-foil)" },
  { globo: "Orgánico", ventas: 2400, fill: "var(--color-organico)" },
  { globo: "Burbuja", ventas: 1500, fill: "var(--color-burbuja)" },
  { globo: "Gigante", ventas: 900, fill: "var(--color-gigante)" },
];
const salesConfig = {
  ventas: { label: "Unidades" },
  latex: { label: "Látex", color: "var(--chart-1)" },
  foil: { label: "Foil", color: "var(--chart-2)" },
  organico: { label: "Orgánico", color: "var(--chart-3)" },
  burbuja: { label: "Burbuja", color: "var(--chart-4)" },
  gigante: { label: "Gigante", color: "var(--chart-5)" },
} satisfies ChartConfig;

export default function ChartDemo() {
  return (
    <>
      <Example title="Barras agrupadas · eventos por mes (pase el cursor)">
        <ChartContainer config={config} className="h-64 w-full">
          <BarChart data={months}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="mes" tickLine={false} axisLine={false} tickMargin={8} tickFormatter={(v) => String(v).slice(0, 3)} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            <Bar dataKey="bodas" fill="var(--color-bodas)" radius={4} />
            <Bar dataKey="corporativos" fill="var(--color-corporativos)" radius={4} />
            <Bar dataKey="cumpleanos" fill="var(--color-cumpleanos)" radius={4} />
          </BarChart>
        </ChartContainer>
      </Example>
      <Example title="Área apilada">
        <ChartContainer config={config} className="h-56 w-full">
          <AreaChart data={months}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="mes" tickLine={false} axisLine={false} tickMargin={8} tickFormatter={(v) => String(v).slice(0, 3)} />
            <ChartTooltip content={<ChartTooltipContent indicator="line" />} />
            <Area dataKey="cumpleanos" type="natural" stackId="a" fill="var(--color-cumpleanos)" fillOpacity={0.4} stroke="var(--color-cumpleanos)" />
            <Area dataKey="corporativos" type="natural" stackId="a" fill="var(--color-corporativos)" fillOpacity={0.4} stroke="var(--color-corporativos)" />
            <Area dataKey="bodas" type="natural" stackId="a" fill="var(--color-bodas)" fillOpacity={0.4} stroke="var(--color-bodas)" />
          </AreaChart>
        </ChartContainer>
      </Example>
      <Example title="Una barra por categoría (chart-1 a chart-5) y línea">
        <div className="grid gap-4 md:grid-cols-2">
          <ChartContainer config={salesConfig} className="h-52 w-full">
            <BarChart data={sales}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="globo" tickLine={false} axisLine={false} tickMargin={8} />
              <ChartTooltip content={<ChartTooltipContent hideLabel />} />
              <Bar dataKey="ventas" radius={6} />
            </BarChart>
          </ChartContainer>
          <ChartContainer config={config} className="h-52 w-full">
            <LineChart data={months}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="mes" tickLine={false} axisLine={false} tickMargin={8} tickFormatter={(v) => String(v).slice(0, 3)} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Line dataKey="bodas" stroke="var(--color-bodas)" strokeWidth={2} dot={false} />
              <Line dataKey="cumpleanos" stroke="var(--color-cumpleanos)" strokeWidth={2} dot={false} />
            </LineChart>
          </ChartContainer>
        </div>
      </Example>
    </>
  );
}
