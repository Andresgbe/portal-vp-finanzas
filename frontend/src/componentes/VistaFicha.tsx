import type { FichaColaborador } from "../api/tipos";
import { formatFecha } from "../utils/formato";
import { Avatar } from "./Avatar";

/** Ficha de una persona. La usan Mi perfil y el Directorio. */
export function VistaFicha({ ficha }: { ficha: FichaColaborador }) {
  const activo = ficha.estado === "activo";

  return (
    <>
      <section className="vidrio perfil-cabecera">
        <Avatar nombre={ficha.nombre} tamano="grande" />
        <div>
          <h1>{ficha.nombre}</h1>
          <p className="subtitulo">{ficha.cargo}</p>
          <div className="pills">
            <span className="pill pill-azul">{ficha.departamento}</span>
            <span className="pill pill-azul">{ficha.nivel}</span>
            <span className={activo ? "pill pill-ok" : "pill pill-neutra"}>{activo ? "Activo" : "Inactivo"}</span>
          </div>
        </div>
      </section>

      <div className="rejilla-dos" style={{ gap: 16 }}>
        <section className="vidrio tarjeta">
          <h2>Datos</h2>
          <div className="datos" style={{ gap: 10 }}>
            <div className="perfil-dato perfil-dato-ancho"><span>Correo</span><strong>{ficha.correo}</strong></div>
            <div className="perfil-dato"><span>País</span><strong>{ficha.pais}</strong></div>
            <div className="perfil-dato"><span>Fecha de ingreso</span><strong>{formatFecha(ficha.fecha_ingreso)}</strong></div>
          </div>
        </section>
        <section className="vidrio tarjeta">
          <h2>Funciones del cargo</h2>
          <ul className="funciones">
            {ficha.funciones.map((funcion) => <li key={funcion}>{funcion}</li>)}
          </ul>
        </section>
      </div>
    </>
  );
}
