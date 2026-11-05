import { api } from "../api/cliente";
import type { FichaColaborador } from "../api/tipos";
import { EstadoCarga, MensajeError } from "../componentes/Estados";
import { VistaFicha } from "../componentes/VistaFicha";
import { useCarga } from "../hooks/useCarga";

export function Perfil() {
  const { datos, error, cargando } = useCarga(() => api<FichaColaborador>("/perfil"), []);

  if (cargando) return <EstadoCarga />;
  if (error) return <MensajeError texto={error} />;
  return datos && <VistaFicha ficha={datos} />;
}
