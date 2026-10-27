import { Upload } from "@/components/bencho/upload-dropzone/Upload";
import "@/components/bencho/upload-dropzone/Upload.css";
import { Example } from "@kit/demo";

export default function UploadDropzoneDemo() {
  return (
    <>
      <Example title="Zona de carga: arrastrar el archivo a la caja (teclado: foco en el archivo y Enter)">
        <div className="bencho flex justify-center p-6"><Upload /></div>
      </Example>
      <Example title="Envío lento y esquina marcada">
        <div className="bencho flex justify-center p-6"><Upload speed={20} bounce={70} corner={8} /></div>
      </Example>
    </>
  );
}
