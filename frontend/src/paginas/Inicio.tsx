import { Navigate } from "react-router-dom";
import { EstadoVacio } from "../componentes/Estados";
import { RUTA_DE_MODULO } from "../sesion/modulos";
import { useSesion } from "../sesion/SesionContext";

/** Lleva a la persona al primer módulo que tenga disponible. */
export function Inicio() {
  const { usuario } = useSesion();
  const primero = usuario?.modulos.find((modulo) => RUTA_DE_MODULO[modulo.codigo]);

  if (!primero) return <EstadoVacio texto="Tu usuario no tiene módulos asignados." />;
  return <Navigate to={RUTA_DE_MODULO[primero.codigo]} replace />;
}
