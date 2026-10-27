import Masonry from "@/components/react-bits/Masonry";
import { Example, picture } from "@kit/demo";
import { useMotionProfile } from "@kit/motion";

const base = [
  ["Arco orgánico", 280, 420], ["Centros de mesa", 200, 300], ["Boda Jazmín", 330, 520], ["Columnas", 160, 360],
  ["Piñata gigante", 40, 300], ["Bautizo", 250, 460], ["Vitrina Lumen", 10, 340], ["Cumpleaños espacial", 300, 400],
  ["Cascada", 180, 480], ["Salón Aurora", 120, 320],
];
const items = base.map(([t, hue, h], i) => ({
  id: i + 1, img: picture(" ", hue as number, 400, h as number), height: h as number, width: 400,
  title: t as string, description: "Galería de montajes", alt: t as string,
}));

export default function MasonryDemo() {
  const { reduced } = useMotionProfile();
  return (
    <>
      <Example title="Muro de montajes con aparición escalonada y zoom al pasar">
        <Masonry items={items} columns={3} gap={12} animateFrom={reduced ? "none" : "bottom"} hoverEffect="zoom"
          captions="hover" revealOnScroll={false} />
      </Example>
      <Example title="Con subtítulos siempre visibles y elevación">
        <Masonry items={items.slice(0, 6)} columns={2} gap={12} animateFrom="none" hoverEffect="lift" captions="always" />
      </Example>
    </>
  );
}
