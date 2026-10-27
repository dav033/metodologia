import { Skeleton } from "@/components/ui/skeleton";
import { Example } from "@kit/demo";

export default function SkeletonDemo() {
  return (
    <>
      <Example title="Tarjeta de evento cargando">
        <div className="flex max-w-sm flex-col gap-3 rounded-xl border border-border p-4">
          <Skeleton className="h-32 w-full rounded-lg" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </Example>
      <Example title="Fila de cliente">
        <div className="flex items-center gap-3">
          <Skeleton className="size-10 rounded-full" />
          <div className="flex flex-col gap-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
      </Example>
      <Example title="Lista de pedidos">
        <div className="flex max-w-md flex-col gap-3">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-9 w-full" />)}
        </div>
      </Example>
    </>
  );
}
