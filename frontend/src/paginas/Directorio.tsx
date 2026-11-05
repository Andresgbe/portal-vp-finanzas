import { Link, useParams } from "react-router-dom";
import { api } from "../api/cliente";
import type { Colaborador, DepartamentoResumen } from "../api/tipos";
import { Avatar } from "../componentes/Avatar";
import { EstadoCarga, EstadoVacio, MensajeError } from "../componentes/Estados";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion/SesionContext";
import { formatFecha } from "../utils/formato";

function ContenidoTarjeta({ persona }: { persona: Colaborador }) {
  return (
    <>
      <div className="persona-cabecera">
        <Avatar nombre={persona.nombre} />
        <div>
          <span className="persona-nombre">{persona.nombre}</span>
          <small>{persona.cargo}</small>
        </div>
      </div>
      {/* El rol Colaborador recibe menos campos: se muestra solo lo que llegó */}
      {persona.nivel && (
        <div className="pills">
          <span className="pill pill-azul">{persona.nivel}</span>
          <span className={persona.estado === "activo" ? "pill pill-ok" : "pill pill-neutra"}>
            {persona.estado === "activo" ? "Activo" : "Inactivo"}
          </span>
        </div>
      )}
      <div className="persona-datos">
        <span>{persona.correo}</span>
        {persona.pais && persona.fecha_ingreso && (
          <span>{persona.pais} · Ingreso {formatFecha(persona.fecha_ingreso)}</span>
        )}
      </div>
    </>
  );
}

/** Directorio del departamento elegido. Pedir uno ajeno por la URL no da acceso: el backend responde 403. */
export function Directorio() {
  const { departamentoId } = useParams();
  const { usuario } = useSesion();

  const departamentos = useCarga(() => api<DepartamentoResumen[]>("/departamentos"), []);
  const personas = useCarga(
    () => api<Colaborador[]>(`/departamentos/${departamentoId}/colaboradores`),
    [departamentoId],
  );

  const departamento = departamentos.datos?.find((d) => String(d.id) === departamentoId);

  // El backend le niega a un Colaborador la ficha de otra persona: no se ofrece el enlace
  const puedeVerFicha = (persona: Colaborador) =>
    usuario!.rol !== "COLABORADOR" || persona.id === usuario!.colaborador_id;

  return (
    <>
      <div className="encabezado" style={{ gap: 8 }}>
        <Link className="volver" to="/departamentos">Volver a departamentos</Link>
        <h1>{departamento?.nombre ?? "Directorio"}</h1>
        {personas.datos && <p className="subtitulo">Directorio · {personas.datos.length} colaboradores</p>}
      </div>

      {personas.error && <MensajeError texto={personas.error} />}
      {personas.cargando && !personas.datos && <EstadoCarga />}
      {personas.datos?.length === 0 && <EstadoVacio texto="Este departamento no tiene colaboradores." />}

      <div className="rejilla-personas">
        {personas.datos?.map((persona) =>
          puedeVerFicha(persona) ? (
            <Link key={persona.id} className="vidrio persona" to={`/departamentos/${departamentoId}/colaboradores/${persona.id}`}>
              <ContenidoTarjeta persona={persona} />
            </Link>
          ) : (
            <article key={persona.id} className="vidrio persona">
              <ContenidoTarjeta persona={persona} />
            </article>
          ),
        )}
      </div>
    </>
  );
}
