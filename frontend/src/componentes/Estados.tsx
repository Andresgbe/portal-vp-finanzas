// Estados que comparten todas las pantallas, para que ninguna quede en blanco.

export function EstadoCarga({ texto = "Cargando…" }: { texto?: string }) {
  return <p className="estado" role="status">{texto}</p>;
}

export function MensajeError({ texto }: { texto: string }) {
  return <p className="estado estado-error" role="alert">{texto}</p>;
}

export function EstadoVacio({ texto }: { texto: string }) {
  return <p className="estado">{texto}</p>;
}
