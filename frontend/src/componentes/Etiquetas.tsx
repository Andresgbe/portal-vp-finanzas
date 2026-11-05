import { NOMBRE_ESTADO, NOMBRE_SEVERIDAD } from "../utils/etiquetas";

// La severidad y el estado siempre llevan texto: nunca se comunican solo con color.

export function PillSeveridad({ severidad }: { severidad: string }) {
  return <span className={`pill pill-punto pill-${severidad}`}>{NOMBRE_SEVERIDAD[severidad] ?? severidad}</span>;
}

const CLASE_ESTADO: Record<string, string> = {
  pendiente: "pill-neutra",
  revisada: "pill-ok",
  descartada: "pill-azul",
};

export function PillEstado({ estado }: { estado: string }) {
  return <span className={`pill ${CLASE_ESTADO[estado] ?? "pill-neutra"}`}>{NOMBRE_ESTADO[estado] ?? estado}</span>;
}
