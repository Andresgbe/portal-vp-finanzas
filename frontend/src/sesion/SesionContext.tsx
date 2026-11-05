import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, ErrorApi, registrarAlExpirarSesion } from "../api/cliente";
import type { Sesion } from "../api/tipos";

interface ValorSesion {
  usuario: Sesion | null;
  cargando: boolean;
  errorCarga: string | null;
  iniciarSesion: (correo: string, password: string) => Promise<void>;
  cerrarSesion: () => Promise<void>;
}

const SesionContext = createContext<ValorSesion | null>(null);

export function SesionProvider({ children }: { children: ReactNode }) {
  // La sesión vive solo en memoria. Al recargar se vuelve a preguntar a /auth/me:
  // el backend es la única fuente de verdad sobre quién eres y qué puedes ver.
  const [usuario, setUsuario] = useState<Sesion | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  useEffect(() => {
    registrarAlExpirarSesion(() => setUsuario(null));

    api<Sesion>("/auth/me")
      .then(setUsuario)
      .catch((error: ErrorApi) => {
        // 401 solo significa que no hay sesión: se muestra el login, no un error
        if (error.status !== 401) setErrorCarga(error.message);
      })
      .finally(() => setCargando(false));
  }, []);

  async function iniciarSesion(correo: string, password: string) {
    setUsuario(await api<Sesion>("/auth/login", { correo, password }));
    setErrorCarga(null);
  }

  async function cerrarSesion() {
    await api<void>("/auth/logout", undefined, "POST");
    setUsuario(null);
  }

  return (
    <SesionContext.Provider value={{ usuario, cargando, errorCarga, iniciarSesion, cerrarSesion }}>
      {children}
    </SesionContext.Provider>
  );
}

export function useSesion(): ValorSesion {
  const valor = useContext(SesionContext);
  if (!valor) throw new Error("useSesion debe usarse dentro de SesionProvider");
  return valor;
}
