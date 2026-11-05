import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, descargar, ErrorApi } from "../api/cliente";
import type { Cajero, Cierre, CierreCreado, Tienda } from "../api/tipos";
import { EstadoCarga, MensajeError } from "../componentes/Estados";
import { useCarga } from "../hooks/useCarga";
import { useSesion } from "../sesion/SesionContext";
import { esNegativo, formatDiferencia, formatFecha, formatFechaHora, formatMonto, normalizarMonto } from "../utils/formato";

function FormularioInhabilitar({ cierre, alCancelar, alInhabilitar }: {
  cierre: Cierre;
  alCancelar: () => void;
  alInhabilitar: () => void;
}) {
  const [motivo, setMotivo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await api<Cierre>(`/cierres/${cierre.id}/inhabilitar`, { motivo });
      alInhabilitar();
    } catch (e) {
      setError((e as ErrorApi).message);
      setEnviando(false);
    }
  }

  return (
    <section className="vidrio tarjeta" aria-labelledby="titulo-inhabilitar">
      <div className="encabezado">
        <h2 id="titulo-inhabilitar">Inhabilitar el cierre #{cierre.id}</h2>
        <p className="subtitulo">
          {cierre.cajero} · {cierre.tienda} · {formatFecha(cierre.fecha)}. El cierre no se borra: queda
          registrado quién lo inhabilitó y por qué, y sus alertas pendientes se descartan.
        </p>
      </div>
      <form className="columna" style={{ gap: 12 }} onSubmit={enviar}>
        <div className="campo">
          <label htmlFor="motivo">Motivo</label>
          <textarea id="motivo" autoFocus placeholder="Explica por qué se inhabilita (mínimo 10 caracteres)." value={motivo} onChange={(e) => setMotivo(e.target.value)} />
        </div>
        {error && <MensajeError texto={error} />}
        <div className="botones">
          <button type="submit" className="boton boton-primario" disabled={enviando}>
            {enviando ? "Inhabilitando…" : "Inhabilitar cierre"}
          </button>
          <button type="button" className="boton boton-secundario" onClick={alCancelar}>Cancelar</button>
        </div>
      </form>
    </section>
  );
}

function FormularioRegistro({ tiendas, alRegistrar }: { tiendas: Tienda[]; alRegistrar: () => void }) {
  const [tiendaId, setTiendaId] = useState("");
  const [cajeroId, setCajeroId] = useState("");
  const [fecha, setFecha] = useState("");
  const [declarado, setDeclarado] = useState("");
  const [sistema, setSistema] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<CierreCreado | null>(null);
  const [enviando, setEnviando] = useState(false);

  // Los cajeros dependen de la tienda: el backend devuelve solo los de esa tienda
  const cajeros = useCarga<Cajero[]>(
    () => (tiendaId ? api<Cajero[]>(`/cajeros?tienda_id=${tiendaId}`) : Promise.resolve([])),
    [tiendaId],
  );

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    setResultado(null);

    const montoDeclarado = normalizarMonto(declarado);
    const montoSistema = normalizarMonto(sistema);
    if (!montoDeclarado || !montoSistema) {
      setError("Escribe los montos como 1.520,50 o 1520,50.");
      return;
    }

    setEnviando(true);
    try {
      const creado = await api<CierreCreado>("/cierres", {
        tienda_id: Number(tiendaId),
        cajero_id: Number(cajeroId),
        fecha,
        // Los montos viajan como texto para que el backend los reciba exactos
        monto_declarado: montoDeclarado,
        monto_sistema: montoSistema,
      });
      setResultado(creado);
      setDeclarado("");
      setSistema("");
      alRegistrar();
    } catch (e) {
      setError((e as ErrorApi).message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="vidrio tarjeta">
      <h2>Registrar cierre</h2>
      <form className="formulario-rejilla" onSubmit={enviar}>
        <div className="campo">
          <label htmlFor="tienda">Tienda</label>
          <select id="tienda" required value={tiendaId} onChange={(e) => { setTiendaId(e.target.value); setCajeroId(""); }}>
            <option value="">Elige una tienda</option>
            {tiendas.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="cajero">Cajero</label>
          <select id="cajero" required disabled={!tiendaId} value={cajeroId} onChange={(e) => setCajeroId(e.target.value)}>
            <option value="">{tiendaId ? "Elige un cajero" : "Falta la tienda"}</option>
            {cajeros.datos?.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="fecha">Fecha</label>
          <input id="fecha" type="date" required value={fecha} onChange={(e) => setFecha(e.target.value)} />
        </div>
        <div className="campo">
          <label htmlFor="declarado">Monto declarado</label>
          <input id="declarado" className="monto-entrada" inputMode="decimal" required placeholder="1.520,00" value={declarado} onChange={(e) => setDeclarado(e.target.value)} />
        </div>
        <div className="campo">
          <label htmlFor="sistema">Monto sistema</label>
          <input id="sistema" className="monto-entrada" inputMode="decimal" required placeholder="1.250,00" value={sistema} onChange={(e) => setSistema(e.target.value)} />
        </div>
        <button type="submit" className="boton boton-primario" disabled={enviando}>
          {enviando ? "Registrando…" : "Registrar cierre"}
        </button>
      </form>

      {error && <MensajeError texto={error} />}
      {resultado && (
        <p className={resultado.alertas_generadas > 0 ? "estado estado-info" : "estado estado-ok"}>
          Cierre #{resultado.id} registrado.{" "}
          {resultado.alertas_generadas > 0
            ? <>Generó {resultado.alertas_generadas} {resultado.alertas_generadas === 1 ? "alerta" : "alertas"}. <Link to="/alertas">Ver alertas</Link></>
            : "No generó alertas."}
        </p>
      )}
    </section>
  );
}

export function Cierres() {
  const { usuario } = useSesion();
  const [tiendaId, setTiendaId] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [soloConAlertas, setSoloConAlertas] = useState(false);
  const [aInhabilitar, setAInhabilitar] = useState<Cierre | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [descargando, setDescargando] = useState(false);
  const [errorDescarga, setErrorDescarga] = useState<string | null>(null);

  // Mostrar el formulario es comodidad: quien decide si puede registrar es el backend (403)
  const puedeRegistrar = usuario?.modulos.find((m) => m.codigo === "CIERRES")?.nivel_acceso === "escritura";

  const tiendas = useCarga(() => api<Tienda[]>("/tiendas"), []);

  // La tabla y el PDF usan los mismos filtros: el reporte siempre coincide con lo que se ve
  const parametros = new URLSearchParams();
  if (tiendaId) parametros.set("tienda_id", tiendaId);
  if (desde) parametros.set("desde", desde);
  if (hasta) parametros.set("hasta", hasta);
  if (soloConAlertas) parametros.set("solo_con_alertas", "true");
  const filtros = parametros.toString();

  const cierres = useCarga(() => api<Cierre[]>(`/cierres?${filtros}`), [filtros]);

  async function descargarReporte() {
    setErrorDescarga(null);
    setDescargando(true);
    try {
      await descargar(`/cierres/reporte.pdf?${filtros}`, "reporte-cierres.pdf");
    } catch (e) {
      setErrorDescarga((e as ErrorApi).message);
    } finally {
      setDescargando(false);
    }
  }

  return (
    <>
      <div className="encabezado">
        <h1>Cierres de caja</h1>
        <p className="subtitulo">
          {puedeRegistrar
            ? "Al registrar un cierre, el sistema lo evalúa de inmediato y genera las alertas que correspondan."
            : "Consulta de los cierres registrados por Tesorería."}
        </p>
      </div>

      {puedeRegistrar && tiendas.datos && <FormularioRegistro tiendas={tiendas.datos} alRegistrar={cierres.recargar} />}

      {aviso && <p className="estado estado-ok" role="status">{aviso}</p>}

      {aInhabilitar && (
        <FormularioInhabilitar
          key={aInhabilitar.id}
          cierre={aInhabilitar}
          alCancelar={() => setAInhabilitar(null)}
          alInhabilitar={() => {
            setAviso(`Cierre #${aInhabilitar.id} inhabilitado.`);
            setAInhabilitar(null);
            cierres.recargar();
          }}
        />
      )}

      <section className="vidrio tabla-marco">
        <form className="formulario-rejilla" style={{ padding: "16px 20px" }} onSubmit={(e) => e.preventDefault()}>
          <div className="campo">
            <label htmlFor="f-tienda">Tienda</label>
            <select id="f-tienda" value={tiendaId} onChange={(e) => setTiendaId(e.target.value)}>
              <option value="">Todas</option>
              {tiendas.datos?.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="f-desde">Desde</label>
            <input id="f-desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
          </div>
          <div className="campo">
            <label htmlFor="f-hasta">Hasta</label>
            <input id="f-hasta" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
          </div>
          <label className="casilla">
            <input type="checkbox" checked={soloConAlertas} onChange={(e) => setSoloConAlertas(e.target.checked)} />
            Solo con alertas
          </label>
          <button type="button" className="boton boton-secundario" disabled={descargando} onClick={descargarReporte}>
            {descargando ? "Generando…" : "Descargar PDF"}
          </button>
        </form>

        {errorDescarga && <div className="filtros"><MensajeError texto={errorDescarga} /></div>}

        {cierres.error && <div className="filtros"><MensajeError texto={cierres.error} /></div>}
        {cierres.cargando && !cierres.datos && <div className="filtros"><EstadoCarga /></div>}

        {cierres.datos && (
          <div className="tabla-scroll">
            <table className="tabla-cierres">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tienda</th>
                  <th>Cajero</th>
                  <th className="num">Declarado</th>
                  <th className="num">Sistema</th>
                  <th className="num">Diferencia</th>
                  <th>Alertas</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {cierres.datos.map((c) => (
                  <tr key={c.id} className={c.estado === "inhabilitado" ? "fila-inhabilitada" : undefined}>
                    <td className="fecha">{formatFecha(c.fecha)}</td>
                    <td>{c.tienda}</td>
                    <td>{c.cajero}</td>
                    <td className="num">{formatMonto(c.monto_declarado)}</td>
                    <td className="num">{formatMonto(c.monto_sistema)}</td>
                    <td className={esNegativo(c.diferencia) ? "num negativo" : "num"}>{formatDiferencia(c.diferencia)}</td>
                    <td>
                      {c.alertas.length === 0
                        ? <span className="pill pill-neutra">Sin alertas</span>
                        : <span className="pill pill-alta">{c.alertas.length === 1 ? "1 alerta" : `${c.alertas.length} alertas`}</span>}
                    </td>
                    <td>
                      {c.estado === "activo" ? (
                        <div className="estado-cierre">
                          <span className="pill pill-ok">Activo</span>
                          {/* El backend decide si se puede: tabla permiso_accion y segregación de funciones */}
                          {c.puede_inhabilitar && (
                            <button type="button" className="ver ver-boton" onClick={() => { setAviso(null); setAInhabilitar(c); }}>
                              Inhabilitar
                            </button>
                          )}
                        </div>
                      ) : (
                        <div className="baja-cierre">
                          <span className="pill pill-neutra">Inhabilitado</span>
                          <small>{c.motivo_inhabilitacion}</small>
                          {c.inhabilitado_en && <small>{c.inhabilitado_por} · {formatFechaHora(c.inhabilitado_en)}</small>}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {cierres.datos.length === 0 && <p className="tabla-vacia">No hay cierres con esos filtros.</p>}
          </div>
        )}
      </section>
    </>
  );
}
