import type { ReactNode } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { EstadoCarga, MensajeError } from "../componentes/Estados";
import { useSesion } from "./SesionContext";

/** Sin sesión, redirige al login. */
export function RutaProtegida() {
  const { usuario, cargando, errorCarga } = useSesion();

  if (cargando) return <main className="centrado"><EstadoCarga texto="Verificando tu sesión…" /></main>;
  if (errorCarga) return <main className="centrado"><MensajeError texto={errorCarga} /></main>;
  if (!usuario) return <Navigate to="/login" replace />;
  return <Outlet />;
}

/**
 * Evita mostrar una pantalla de un módulo que la persona no tiene.
 * Es solo comodidad visual: aunque alguien la saltara, el backend respondería 403.
 */
export function RutaModulo({ codigo, children }: { codigo: string; children: ReactNode }) {
  const { usuario } = useSesion();

  if (!usuario?.modulos.some((modulo) => modulo.codigo === codigo)) {
    return <MensajeError texto="No tienes acceso a este módulo." />;
  }
  return <>{children}</>;
}
