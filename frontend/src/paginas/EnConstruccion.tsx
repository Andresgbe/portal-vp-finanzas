import { EstadoVacio } from "../componentes/Estados";

// Temporal: cada módulo la reemplaza con su pantalla real (tickets #19, #20 y #21).
export function EnConstruccion({ titulo }: { titulo: string }) {
  return (
    <>
      <h1>{titulo}</h1>
      <EstadoVacio texto="Esta pantalla está en construcción." />
    </>
  );
}
