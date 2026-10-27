import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "@/components/ui/pagination";
import { Example } from "@kit/demo";

export default function PaginationDemo() {
  return (
    <>
      <Example title="Listado de pedidos, página 2 de 12">
        <Pagination>
          <PaginationContent>
            <PaginationItem><PaginationPrevious href="#1" /></PaginationItem>
            <PaginationItem><PaginationLink href="#1">1</PaginationLink></PaginationItem>
            <PaginationItem><PaginationLink href="#2" isActive>2</PaginationLink></PaginationItem>
            <PaginationItem><PaginationLink href="#3">3</PaginationLink></PaginationItem>
            <PaginationItem><PaginationEllipsis /></PaginationItem>
            <PaginationItem><PaginationLink href="#12">12</PaginationLink></PaginationItem>
            <PaginationItem><PaginationNext href="#3" /></PaginationItem>
          </PaginationContent>
        </Pagination>
      </Example>
      <Example title="Primera página (anterior deshabilitado)">
        <Pagination>
          <PaginationContent>
            <PaginationItem><PaginationPrevious href="#" aria-disabled className="pointer-events-none opacity-50" /></PaginationItem>
            <PaginationItem><PaginationLink href="#1" isActive>1</PaginationLink></PaginationItem>
            <PaginationItem><PaginationLink href="#2">2</PaginationLink></PaginationItem>
            <PaginationItem><PaginationNext href="#2" /></PaginationItem>
          </PaginationContent>
        </Pagination>
      </Example>
    </>
  );
}
