import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/cliente";
import type { Colaborador, DepartamentoResumen } from "../api/tipos";
import { Avatar } from "../componentes/Avatar";
import { Chips } from "../componentes/Chips";
import { EstadoCarga, EstadoVacio, MensajeError } from "../componentes/Estados";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion/SesionContext";
import { formatFecha } from "../utils/formato";

const TODOS = "";

function ContenidoTarjeta({ persona, mostrarDepartamento }: { persona: Colaborador; mostrarDepartamento: boolean }) {
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
          {mostrarDepartamento && <span className="pill pill-azul">{persona.departamento}</span>}
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

async function cargarColaboradores(filtro: string): Promise<Colaborador[]> {
  if (filtro !== TODOS) return api<Colaborador[]>(`/departamentos/${filtro}/colaboradores`);

  // La API entrega los colaboradores por departamento: "Todos" los pide uno por uno
  const departamentos = await api<DepartamentoResumen[]>("/departamentos");
  const listas = await Promise.all(
    departamentos.map((d) => api<Colaborador[]>(`/departamentos/${d.id}/colaboradores`)),
  );
  return listas.flat();
}

export function Directorio() {
  const { usuario } = useSesion();
  const [parametros] = useSearchParams();

  // Si se llega desde la pestaña Departamentos, se abre el departamento elegido.
  // Pedir uno ajeno por la URL no da acceso: el backend respondería 403.
  const [filtro, setFiltro] = useState(
    parametros.get("departamento") ?? (usuario!.rol === "ADMIN" ? TODOS : String(usuario!.departamento_id)),
  );

  const departamentos = useCarga(() => api<DepartamentoResumen[]>("/departamentos"), []);
  const personas = useCarga(() => cargarColaboradores(filtro), [filtro]);

  const lista = departamentos.datos ?? [];
  const elegido = lista.find((d) => String(d.id) === filtro);

  // Los filtros salen de lo que devuelve el backend: solo el Administrador recibe más de uno
  const opciones = [
    { valor: TODOS, texto: `Todos (${lista.reduce((suma, d) => suma + d.total_colaboradores, 0)})` },
    ...lista.map((d) => ({ valor: String(d.id), texto: `${d.nombre} (${d.total_colaboradores})` })),
  ];

  // El backend le niega a un Colaborador la ficha de otra persona: no se ofrece el enlace
  const puedeVerFicha = (persona: Colaborador) =>
    usuario!.rol !== "COLABORADOR" || persona.id === usuario!.colaborador_id;

  return (
    <>
      <div className="encabezado">
        <h1>Directorio</h1>
        {personas.datos && !personas.cargando && (
          <p className="subtitulo">
            {filtro === TODOS ? "Todos los departamentos" : elegido?.nombre} · {personas.datos.length} colaboradores
          </p>
        )}
      </div>

      {lista.length > 1 && (
        <Chips titulo="Filtrar por departamento" opciones={opciones} valor={filtro} alCambiar={setFiltro} />
      )}

      {personas.error && <MensajeError texto={personas.error} />}
      {personas.cargando && !personas.datos && <EstadoCarga />}
      {personas.datos?.length === 0 && <EstadoVacio texto="Este departamento no tiene colaboradores." />}

      {!personas.error && (
        <div className="rejilla-personas">
          {personas.datos?.map((persona) =>
            puedeVerFicha(persona) ? (
              <Link key={persona.id} className="vidrio persona" to={`/directorio/${persona.id}`}>
                <ContenidoTarjeta persona={persona} mostrarDepartamento={filtro === TODOS} />
              </Link>
            ) : (
              <article key={persona.id} className="vidrio persona">
                <ContenidoTarjeta persona={persona} mostrarDepartamento={false} />
              </article>
            ),
          )}
        </div>
      )}
    </>
  );
}
