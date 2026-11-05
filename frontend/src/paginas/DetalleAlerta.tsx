import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ErrorApi } from "../api/cliente";
import type { AlertaDetalle } from "../api/tipos";
import { ComparacionDigitos } from "../componentes/ComparacionDigitos";
import { EstadoCarga, MensajeError } from "../componentes/Estados";
import { PillEstado, PillSeveridad } from "../componentes/Etiquetas";
import { useCarga } from "../hooks/useCarga";
import { NOMBRE_ESTADO, NOMBRE_REGLA } from "../utils/etiquetas";
import { formatDiferencia, formatFecha, formatFechaHora, formatMonto } from "../utils/formato";

function FormularioGestion({ alertaId, alGestionar, alConflicto }: {
  alertaId: number;
  alGestionar: (alerta: AlertaDetalle) => void;
  alConflicto: () => void;
}) {
  const [comentario, setComentario] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function gestionar(estado: "revisada" | "descartada") {
    setError(null);
    setEnviando(true);
    try {
      alGestionar(await api<AlertaDetalle>(`/alertas/${alertaId}/gestion`, { estado, comentario }));
    } catch (e) {
      const fallo = e as ErrorApi;
      setError(fallo.message);
      // 409: otra persona la gestionó mientras tanto. Se recarga para mostrar el estado real.
      if (fallo.status === 409) alConflicto();
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="columna" style={{ gap: 12 }}>
      <div className="campo">
        <label htmlFor="comentario">Comentario</label>
        <textarea
          id="comentario"
          placeholder="Explica qué revisaste y qué concluiste (mínimo 10 caracteres)."
          value={comentario}
          onChange={(e) => setComentario(e.target.value)}
        />
      </div>
      {error && <MensajeError texto={error} />}
      <div className="botones">
        <button type="button" className="boton boton-primario" disabled={enviando} onClick={() => gestionar("revisada")}>
          Marcar como revisada
        </button>
        <button type="button" className="boton boton-secundario" disabled={enviando} onClick={() => gestionar("descartada")}>
          Descartar
        </button>
      </div>
    </div>
  );
}

export function DetalleAlerta() {
  const { id } = useParams();
  const { datos: alerta, setDatos, error, cargando, recargar } = useCarga(
    () => api<AlertaDetalle>(`/alertas/${id}`),
    [id],
  );

  if (cargando && !alerta) return <EstadoCarga />;
  if (error && !alerta) return (
    <>
      <Link className="volver" to="/alertas">Volver a alertas</Link>
      <MensajeError texto={error} />
    </>
  );
  if (!alerta) return null;

  return (
    <>
      <div className="encabezado" style={{ gap: 8 }}>
        <Link className="volver" to="/alertas">Volver a alertas</Link>
        <div className="titulo-alerta">
          <h1>Alerta #{alerta.id} · {NOMBRE_REGLA[alerta.regla] ?? alerta.regla}</h1>
          <PillSeveridad severidad={alerta.severidad} />
          <PillEstado estado={alerta.estado} />
        </div>
      </div>

      <div className="rejilla-dos">
        <div className="columna">
          {alerta.regla === "TRANSPOSICION" && (
            <section className="vidrio tarjeta">
              <div className="encabezado">
                <h2>Los dos montos, dígito a dígito</h2>
                <p className="subtitulo">Son iguales salvo dos dígitos vecinos intercambiados.</p>
              </div>
              <ComparacionDigitos declarado={alerta.monto_declarado} sistema={alerta.monto_sistema} />
            </section>
          )}

          <section className="vidrio tarjeta">
            <h2>Cierre #{alerta.cierre_id}</h2>
            <div className="datos">
              <div className="dato"><span>Fecha</span><strong>{formatFecha(alerta.fecha_cierre)}</strong></div>
              <div className="dato"><span>Tienda</span><strong>{alerta.tienda}</strong></div>
              <div className="dato"><span>Cajero</span><strong>{alerta.cajero}</strong></div>
              <div className="dato"><span>Declarado</span><strong className="num" style={{ textAlign: "left" }}>{formatMonto(alerta.monto_declarado)}</strong></div>
              <div className="dato"><span>Sistema</span><strong className="num" style={{ textAlign: "left" }}>{formatMonto(alerta.monto_sistema)}</strong></div>
              <div className="dato"><span>Diferencia</span><strong className="num" style={{ textAlign: "left" }}>{formatDiferencia(alerta.diferencia)}</strong></div>
            </div>
            <p className="subtitulo">{alerta.detalle}</p>
          </section>
        </div>

        <div className="columna">
          <section className="vidrio tarjeta">
            <h2>Gestionar alerta</h2>
            {/* El backend decide si se puede y explica por qué no. Aunque se forzara
                el formulario, el endpoint respondería 403 o 409. */}
            {alerta.puede_gestionar ? (
              <FormularioGestion alertaId={alerta.id} alGestionar={setDatos} alConflicto={recargar} />
            ) : (
              <p className="estado estado-info">{alerta.motivo_no_gestionable}</p>
            )}
          </section>

          <section className="vidrio tarjeta">
            <h2>Historial</h2>
            <ol className="linea-tiempo">
              {alerta.historial.map((evento, i) => (
                <li key={i}>
                  <strong>{evento.estado_anterior ? `${NOMBRE_ESTADO[evento.estado_anterior]} → ${NOMBRE_ESTADO[evento.estado_nuevo]}` : `Alerta creada · ${NOMBRE_ESTADO[evento.estado_nuevo]}`}</strong>
                  <span>{evento.comentario}</span>
                  <small>{evento.usuario} · {formatFechaHora(evento.fecha)}</small>
                </li>
              ))}
            </ol>
          </section>
        </div>
      </div>
    </>
  );
}
