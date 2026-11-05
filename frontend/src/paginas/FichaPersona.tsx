import { Link, useParams } from "react-router-dom";
import { api } from "../api/cliente";
import type { FichaColaborador } from "../api/tipos";
import { EstadoCarga, MensajeError } from "../componentes/Estados";
import { VistaFicha } from "../componentes/VistaFicha";
import { useCarga } from "../hooks/useCarga";

export function FichaPersona() {
  const { id } = useParams();
  const { datos, error, cargando } = useCarga(() => api<FichaColaborador>(`/colaboradores/${id}`), [id]);

  return (
    <>
      <Link className="volver" to="/directorio">Volver al directorio</Link>
      {cargando && <EstadoCarga />}
      {error && <MensajeError texto={error} />}
      {datos && !cargando && <VistaFicha ficha={datos} />}
    </>
  );
}
