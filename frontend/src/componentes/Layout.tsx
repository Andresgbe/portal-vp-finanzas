import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { ErrorApi } from "../api/cliente";
import { RUTA_DE_MODULO } from "../sesion/modulos";
import { useSesion } from "../sesion/SesionContext";
import { Avatar } from "./Avatar";
import { MensajeError } from "./Estados";
import { IconoModulo } from "./IconoModulo";

const NOMBRE_ROL = {
  ADMIN: "Administrador",
  JEFE_DEPTO: "Jefe de departamento",
  COLABORADOR: "Colaborador",
};

export function Layout() {
  const { usuario, cerrarSesion } = useSesion();
  const [error, setError] = useState<string | null>(null);

  if (!usuario) return null;

  async function salir() {
    setError(null);
    try {
      await cerrarSesion();
    } catch (e) {
      setError((e as ErrorApi).message);
    }
  }

  return (
    <div className="marco">
      <aside className="lateral">
        <div className="marca">
          <span className="marca-sello" aria-hidden="true">VP</span>
          <div>
            <div className="marca-nombre">Portal interno</div>
            <div className="marca-area">VP de Finanzas</div>
          </div>
        </div>

        {/* El menú sale de lo que devuelve el backend, no de un rol escrito aquí */}
        <nav aria-label="Módulos" className="menu">
          {usuario.modulos
            .filter((modulo) => RUTA_DE_MODULO[modulo.codigo])
            .map((modulo) => (
              <NavLink key={modulo.codigo} to={RUTA_DE_MODULO[modulo.codigo]} className="enlace-menu">
                <IconoModulo codigo={modulo.codigo} />
                {modulo.nombre}
              </NavLink>
            ))}
        </nav>

        <div className="usuario">
          <div className="usuario-fila">
            <Avatar nombre={usuario.nombre} />
            <div className="usuario-datos">
              <strong>{usuario.nombre}</strong>
              <span>{NOMBRE_ROL[usuario.rol]} · {usuario.departamento}</span>
            </div>
          </div>
          <button type="button" className="enlace-boton" onClick={salir}>Cerrar sesión</button>
        </div>
      </aside>

      <main className="contenido">
        {error && <MensajeError texto={error} />}
        <Outlet />
      </main>
    </div>
  );
}
