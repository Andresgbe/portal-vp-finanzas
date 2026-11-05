import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/cliente";
import type { Alerta, ResumenAlertas } from "../api/tipos";
import { Avatar } from "../componentes/Avatar";
import { EstadoCarga, MensajeError } from "../componentes/Estados";
import { PillEstado, PillSeveridad } from "../componentes/Etiquetas";
import { FiltroDesplegable } from "../componentes/FiltroDesplegable";
import { useCarga } from "../hooks/useCarga";
import { NOMBRE_ESTADO, NOMBRE_REGLA, NOMBRE_SEVERIDAD } from "../utils/etiquetas";
import { esNegativo, formatDiferencia, formatFecha } from "../utils/formato";

function opcionesDe(nombres: Record<string, string>, textoTodas: string) {
  return [{ valor: "", texto: textoTodas }, ...Object.entries(nombres).map(([valor, texto]) => ({ valor, texto }))];
}

function Resumen({ resumen }: { resumen: ResumenAlertas }) {
  const pendientes = resumen.por_estado.find((c) => c.clave === "pendiente")?.total ?? 0;
  const totalAlertas = resumen.por_regla.reduce((suma, c) => suma + c.total, 0);
  const reglas = [...resumen.por_regla].sort((a, b) => b.total - a.total);

  return (
    <section aria-label="Resumen" className="rejilla">
      <div className="vidrio tarjeta">
        <div className="etiqueta">Pendientes</div>
        <div className="total-grande">{pendientes}</div>
        <div className="barra-severidad" aria-hidden="true">
          {resumen.por_severidad_pendientes.map((c) => (
            <span key={c.clave} style={{ flexGrow: c.total, background: `var(--${c.clave}-barra, var(--baja))` }} />
          ))}
        </div>
        <div className="pills">
          {resumen.por_severidad_pendientes.map((c) => (
            <span key={c.clave} className={`pill pill-punto pill-${c.clave}`}>{c.total} {c.clave}</span>
          ))}
        </div>
      </div>

      <div className="vidrio tarjeta">
        <div className="etiqueta">Por regla</div>
        {reglas.map((c) => (
          <div key={c.clave}>
            <div className="fila-conteo"><span>{NOMBRE_REGLA[c.clave] ?? c.clave}</span><strong>{c.total}</strong></div>
            <div className="barra" aria-hidden="true"><span style={{ width: `${(c.total / totalAlertas) * 100}%` }} /></div>
          </div>
        ))}
      </div>

      <div className="vidrio tarjeta">
        <div className="etiqueta">Cajeros con más alertas abiertas</div>
        {resumen.cajeros_con_mas_alertas.slice(0, 3).map((c) => (
          <div key={c.cajero_id} className="persona-celda">
            <Avatar nombre={c.cajero} tamano="chico" />
            <div style={{ flexGrow: 1 }}><span>{c.cajero}</span><small>{c.tienda}</small></div>
            <strong>{c.alertas_abiertas}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Alertas() {
  const [estado, setEstado] = useState("");
  const [regla, setRegla] = useState("");
  const [severidad, setSeveridad] = useState("");

  const resumen = useCarga(() => api<ResumenAlertas>("/alertas/resumen"), []);
  const alertas = useCarga(() => {
    // Los filtros los aplica el backend: el cliente nunca recibe de más
    const parametros = new URLSearchParams();
    if (estado) parametros.set("estado", estado);
    if (regla) parametros.set("regla", regla);
    if (severidad) parametros.set("severidad", severidad);
    return api<Alerta[]>(`/alertas?${parametros}`);
  }, [estado, regla, severidad]);

  return (
    <>
      <div className="encabezado">
        <h1>Alertas de anomalías</h1>
        <p className="subtitulo">Primero lo más urgente: pendientes y de mayor severidad.</p>
      </div>

      {resumen.error && <MensajeError texto={resumen.error} />}
      {resumen.datos && <Resumen resumen={resumen.datos} />}

      <section className="vidrio tabla-marco">
        <div className="filtros">
          <FiltroDesplegable titulo="Estado" opciones={opcionesDe(NOMBRE_ESTADO, "Todos")} valor={estado} alCambiar={setEstado} />
          <FiltroDesplegable titulo="Regla" opciones={opcionesDe(NOMBRE_REGLA, "Todas")} valor={regla} alCambiar={setRegla} />
          <FiltroDesplegable titulo="Severidad" opciones={opcionesDe(NOMBRE_SEVERIDAD, "Todas")} valor={severidad} alCambiar={setSeveridad} />
        </div>

        {alertas.error && <div className="filtros"><MensajeError texto={alertas.error} /></div>}
        {alertas.cargando && !alertas.datos && <div className="filtros"><EstadoCarga /></div>}

        {alertas.datos && (
          <div className="tabla-scroll">
            <table>
              <thead>
                <tr>
                  <th>Severidad</th>
                  <th>Regla</th>
                  <th>Fecha</th>
                  <th>Cajero</th>
                  <th className="num">Diferencia</th>
                  <th>Estado</th>
                  <th><span className="oculto">Acción</span></th>
                </tr>
              </thead>
              <tbody>
                {alertas.datos.map((a) => (
                  <tr key={a.id}>
                    <td><PillSeveridad severidad={a.severidad} /></td>
                    <td>{NOMBRE_REGLA[a.regla] ?? a.regla}</td>
                    <td className="fecha">{formatFecha(a.fecha_cierre)}</td>
                    <td>
                      <div className="persona-celda">
                        <Avatar nombre={a.cajero} tamano="chico" />
                        <div><span>{a.cajero}</span><small>{a.tienda}</small></div>
                      </div>
                    </td>
                    <td className={esNegativo(a.diferencia) ? "num negativo" : "num"}>{formatDiferencia(a.diferencia)}</td>
                    <td><PillEstado estado={a.estado} /></td>
                    <td className="num"><Link className="ver" to={`/alertas/${a.id}`}>Ver detalle</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {alertas.datos.length === 0 && <p className="tabla-vacia">No hay alertas con esos filtros.</p>}
          </div>
        )}
      </section>
    </>
  );
}
