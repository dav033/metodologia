import { AnimateIcon } from "@animate-ui/react/icons";
import { Bell } from "@/components/animate-ui/icons/bell";
import { Check } from "@/components/animate-ui/icons/check";
import { Settings } from "@/components/animate-ui/icons/settings";
import { Heart } from "@/components/animate-ui/icons/heart";
import { Trash2 } from "@/components/animate-ui/icons/trash-2";
import { Search } from "@/components/animate-ui/icons/search";
import { Example, Row } from "@kit/demo";

const icons = [["Avisos", Bell], ["Aprobado", Check], ["Ajustes", Settings], ["Favorito", Heart], ["Eliminar", Trash2], ["Buscar", Search]] as const;

export default function AnimatedIconsDemo() {
  return (
    <>
      <Example title="Animan al pasar el cursor (animateOnHover)">
        <Row className="gap-8">
          {icons.map(([label, Icon]) => (
            <div key={label} className="flex flex-col items-center gap-2 text-foreground">
              <Icon animateOnHover size={28} />
              <span className="text-xs text-muted-foreground">{label}</span>
            </div>
          ))}
        </Row>
      </Example>
      <Example title="AnimateIcon dentro de un botón: anima al pasar sobre todo el botón">
        <Row>
          <AnimateIcon animateOnHover>
            <button className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
              <Bell size={16} /> Notificar al cliente
            </button>
          </AnimateIcon>
          <AnimateIcon animateOnHover>
            <button className="inline-flex items-center gap-2 rounded-lg border border-input px-4 py-2 text-sm text-foreground">
              <Trash2 size={16} /> Cancelar pedido
            </button>
          </AnimateIcon>
        </Row>
      </Example>
    </>
  );
}
