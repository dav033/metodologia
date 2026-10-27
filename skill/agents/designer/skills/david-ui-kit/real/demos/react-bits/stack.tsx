import Stack from "@/components/react-bits/Stack";
import { Effect } from "@kit/effect";
import { Example, picture } from "@kit/demo";

const cards = ["Salón Aurora", "Arco orgánico", "Boda Jazmín", "Cumbre", "Mirador"].map((t, i) => (
  <img key={t} src={picture(t, 40 + i * 60, 420, 420)} alt={t} draggable={false} />
));

export default function StackDemo() {
  return (
    <>
      <Example title="Abanico de fotos: arrastra la de arriba o haz clic para enviarla al fondo">
        <div className="flex h-80 items-center justify-center rounded-xl border border-input bg-background">
          <Stack cards={cards} layout="fan" sendToBackOnClick style={{ width: 220, height: 220 }} />
        </div>
      </Example>
      <Example title="Mazo con avance automático">
        <Effect className="flex h-[26rem] items-start justify-center rounded-xl border border-input bg-background pt-8"
          fallback={<div className="flex size-full items-center justify-center"><img src={picture("Salón Aurora", 40, 420, 420)} alt="Salón Aurora" className="size-52 rounded-2xl" /></div>}>
          <Stack cards={cards} layout="deck" autoplay autoplayDelay={2500} pauseOnHover style={{ width: 200, height: 200 }} />
        </Effect>
      </Example>
    </>
  );
}
