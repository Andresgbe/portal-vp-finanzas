import { Link } from "react-router-dom";
import { api } from "../api/cliente";
import type { DepartamentoResumen } from "../api/tipos";
import { EstadoCarga, EstadoVacio, MensajeError } from "../componentes/Estados";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion/SesionContext";

export function Departamentos() {
  const { usuario } = useSesion();
  // El backend decide cuáles devuelve: los 4 al Administrador, solo el propio a los demás
  const { datos, error, cargando } = useCarga(() => api<DepartamentoResumen[]>("/departamentos"), []);

  const veTodos = usuario!.rol === "ADMIN";

  return (
    <>
      <div className="encabezado">
        <h1>Departamentos</h1>
        <p className="subtitulo">
          {veTodos ? "Departamentos de la Vicepresidencia de Finanzas." : "Tu departamento dentro de la Vicepresidencia de Finanzas."}
        </p>
      </div>

      {error && <MensajeError texto={error} />}
      {cargando && !datos && <EstadoCarga />}
      {datos?.length === 0 && <EstadoVacio texto="No hay departamentos para mostrar." />}

      <div className="rejilla-personas">
        {datos?.map((departamento) => (
          <Link key={departamento.id} className="vidrio persona" to={`/directorio?departamento=${departamento.id}`}>
            <h2>{departamento.nombre}</h2>
            <p className="subtitulo">{departamento.descripcion}</p>
            <div className="pills">
              <span className="pill pill-azul">{departamento.total_colaboradores} colaboradores</span>
              <span className="pill pill-ok">{departamento.activos} activos</span>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
