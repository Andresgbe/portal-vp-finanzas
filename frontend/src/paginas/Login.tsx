import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { ErrorApi } from "../api/cliente";
import { EstadoCarga, MensajeError } from "../componentes/Estados";
import { useSesion } from "../sesion/SesionContext";

export function Login() {
  const { usuario, cargando, iniciarSesion } = useSesion();
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [claveVisible, setClaveVisible] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (cargando) return <main className="login"><EstadoCarga /></main>;
  if (usuario) return <Navigate to="/" replace />;

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await iniciarSesion(correo, password);
    } catch (e) {
      setError((e as ErrorApi).message);
      setPassword("");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="login">
      <span className="login-luz login-luz-1" aria-hidden="true" />
      <span className="login-luz login-luz-2" aria-hidden="true" />
      <span className="login-luz login-luz-3" aria-hidden="true" />

      <main className="login-tarjeta">
        <header>
          <div className="login-area">Vicepresidencia de Finanzas</div>
          <h1>Portal interno</h1>
        </header>

        <form onSubmit={enviar} className="login-form">
          <div className="campo">
            <label htmlFor="correo">Correo</label>
            <input
              id="correo"
              type="email"
              autoComplete="username"
              required
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
            />
          </div>

          <div className="campo">
            <label htmlFor="password">Contraseña</label>
            <div className="clave">
              {/* Mostrar la clave solo cambia el tipo del campo: no se guarda en ningún lado */}
              <input
                id="password"
                type={claveVisible ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="clave-ojo"
                aria-label={claveVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
                aria-pressed={claveVisible}
                onClick={() => setClaveVisible(!claveVisible)}
              >
                <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  {claveVisible ? (
                    <>
                      <path d="M3 3l18 18" />
                      <path d="M10.6 5.2A10 10 0 0 1 12 5c6 0 9.5 7 9.5 7a16 16 0 0 1-3.1 3.9" />
                      <path d="M6.5 6.7A16 16 0 0 0 2.5 12S6 19 12 19a9.6 9.6 0 0 0 4.2-1" />
                      <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
                    </>
                  ) : (
                    <>
                      <path d="M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7z" />
                      <circle cx="12" cy="12" r="3" />
                    </>
                  )}
                </svg>
              </button>
            </div>
          </div>

          {error && <MensajeError texto={error} />}

          <button type="submit" className="login-entrar" disabled={enviando}>
            {enviando ? "Entrando…" : "Iniciar sesión"}
          </button>
        </form>

        <p className="login-nota">Todos los datos de este portal son ficticios.</p>
      </main>
    </div>
  );
}
