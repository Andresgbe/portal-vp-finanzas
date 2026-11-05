import { useState } from "react";
import { api } from "../api/cliente";
import type { DepartamentoResumen, Estructura as DatosEstructura } from "../api/tipos";
import { EstadoCarga, EstadoVacio, MensajeError } from "../componentes/Estados";
import { SelectorDepartamento } from "../componentes/SelectorDepartamento";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion/SesionContext";

export function Estructura() {
  const { usuario } = useSesion();
  const [departamentoId, setDepartamentoId] = useState(usuario!.departamento_id);

  const departamentos = useCarga(() => api<DepartamentoResumen[]>("/departamentos"), []);
  const { datos, error, cargando } = useCarga(
    () => api<DatosEstructura>(`/departamentos/${departamentoId}/estructura`),
    [departamentoId],
  );

  return (
    <>
      <div className="encabezado">
        <h1>Estructura organizacional</h1>
        {datos && <p className="subtitulo">{datos.departamento.nombre} · cargos del nivel más alto al más bajo</p>}
      </div>

      {departamentos.datos && (
        <SelectorDepartamento departamentos={departamentos.datos} valor={departamentoId} alCambiar={setDepartamentoId} />
      )}

      {error && <MensajeError texto={error} />}
      {cargando && !datos && <EstadoCarga />}
      {datos?.cargos.length === 0 && <EstadoVacio texto="Este departamento no tiene cargos." />}

      <div className="lista-cargos">
        {datos?.cargos.map((cargo) => (
          <section key={cargo.id} className="vidrio cargo">
            <div className="cargo-info">
              <h2>{cargo.nombre}</h2>
              <div><span className="pill pill-azul">{cargo.nivel}</span></div>
              <span className="ocupantes">{cargo.ocupantes === 1 ? "1 ocupante" : `${cargo.ocupantes} ocupantes`}</span>
            </div>
            <ul>
              {cargo.funciones.map((funcion) => <li key={funcion}>{funcion}</li>)}
            </ul>
          </section>
        ))}
      </div>
    </>
  );
}
