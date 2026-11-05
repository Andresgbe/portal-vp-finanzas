import { iniciales } from "../utils/formato";

export function Avatar({ nombre, tamano = "mediano" }: { nombre: string; tamano?: "chico" | "mediano" | "grande" }) {
  return <span className={`avatar avatar-${tamano}`} aria-hidden="true">{iniciales(nombre)}</span>;
}
