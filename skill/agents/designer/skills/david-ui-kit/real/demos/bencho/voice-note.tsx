import { VoiceNote } from "@/components/bencho/voice-note/VoiceNote";
import "@/components/bencho/voice-note/VoiceNote.css";
import { Example } from "@kit/demo";

export default function VoiceNoteDemo() {
  return (
    <>
      <Example title="Nota de voz en reposo (mantener pulsado para grabar; el micrófono solo se pide al pulsar, en el marco aislado fallará)">
        <div className="bencho flex justify-center p-6"><VoiceNote /></div>
      </Example>
      <Example title="Más barras y esquina reducida">
        <div className="bencho flex justify-center p-6"><VoiceNote bars={40} corner={14} /></div>
      </Example>
    </>
  );
}
