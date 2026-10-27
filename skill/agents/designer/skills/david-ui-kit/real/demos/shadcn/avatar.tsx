import { Avatar, AvatarBadge, AvatarFallback, AvatarGroup, AvatarGroupCount, AvatarImage } from "@/components/ui/avatar";
import { Example, Row, picture } from "@kit/demo";

export default function AvatarDemo() {
  return (
    <>
      <Example title="Tamaños con imagen">
        <Row>
          <Avatar size="sm"><AvatarImage src={picture("L", 280, 80, 80)} alt="Laura" /><AvatarFallback>LR</AvatarFallback></Avatar>
          <Avatar><AvatarImage src={picture("C", 200, 80, 80)} alt="Camilo" /><AvatarFallback>CM</AvatarFallback></Avatar>
          <Avatar size="lg"><AvatarImage src={picture("M", 330, 80, 80)} alt="Marta" /><AvatarFallback>MP</AvatarFallback></Avatar>
        </Row>
      </Example>
      <Example title="Iniciales y estado">
        <Row>
          <Avatar><AvatarFallback>JG</AvatarFallback><AvatarBadge className="bg-success" /></Avatar>
          <Avatar size="lg"><AvatarFallback>AS</AvatarFallback><AvatarBadge /></Avatar>
          <Avatar><AvatarImage src="" alt="" /><AvatarFallback>?</AvatarFallback></Avatar>
        </Row>
      </Example>
      <Example title="Grupo de equipo">
        <AvatarGroup>
          <Avatar><AvatarFallback>LR</AvatarFallback></Avatar>
          <Avatar><AvatarFallback>CM</AvatarFallback></Avatar>
          <Avatar><AvatarFallback>MP</AvatarFallback></Avatar>
          <AvatarGroupCount>+5</AvatarGroupCount>
        </AvatarGroup>
      </Example>
    </>
  );
}
