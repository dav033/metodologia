import CircularGallery from "@/components/react-bits/CircularGallery";
import { Effect } from "@kit/effect";
import { Example, picture } from "@kit/demo";

const items = [
  ["Salón Aurora", 280], ["Arco orgánico", 200], ["Boda Jazmín", 330], ["Cumbre corporativa", 160],
  ["Mirador", 40], ["Bautizo Ortiz", 250], ["Columnas", 300], ["Vitrina Lumen", 10],
].map(([text, hue]) => ({ image: picture(text as string, hue as number, 640, 420), text: text as string, alt: text as string }));

export default function CircularGalleryDemo() {
  return (
    <>
      <Example title="Galería curva en WebGL (arrastra o usa la rueda; las imágenes son locales)">
        <Effect className="h-96 overflow-hidden rounded-xl border border-input bg-background"
          fallback={<div className="flex size-full items-center gap-3 overflow-hidden p-4">
            {items.slice(0, 4).map((it) => <img key={it.text} src={it.image} alt={it.alt} className="h-56 flex-none rounded-xl" />)}
          </div>}>
          <CircularGallery items={items} bend={3} textColor="#7a2ee0" borderRadius={0.05} snap />
        </Effect>
      </Example>
      <Example title="Con avance automático y escala de grises">
        <Effect className="h-80 overflow-hidden rounded-xl border border-input bg-background"
          fallback={<div className="flex size-full items-center gap-3 overflow-hidden p-4">
            {items.slice(0, 4).map((it) => <img key={it.text} src={it.image} alt={it.alt} className="h-48 flex-none rounded-xl grayscale" />)}
          </div>}>
          <CircularGallery items={items} bend={-2} autoScroll={0.3} grayscale textColor="#c2410c" />
        </Effect>
      </Example>
    </>
  );
}
