interface Opcion {
  valor: string;
  texto: string;
}

/** Grupo de filtros donde solo una opción está activa. "" significa "todas". */
export function Chips({ titulo, opciones, valor, alCambiar }: {
  titulo: string;
  opciones: Opcion[];
  valor: string;
  alCambiar: (valor: string) => void;
}) {
  return (
    <div role="group" aria-label={titulo} className="grupo-chips">
      {opciones.map((opcion) => (
        <button
          key={opcion.valor}
          type="button"
          className="chip"
          aria-pressed={valor === opcion.valor}
          onClick={() => alCambiar(opcion.valor)}
        >
          {opcion.texto}
        </button>
      ))}
    </div>
  );
}
