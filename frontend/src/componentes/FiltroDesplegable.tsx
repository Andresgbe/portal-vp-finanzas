import { useEffect, useRef, useState } from "react";

interface Opcion {
  valor: string;
  texto: string;
}

/** Botón que despliega las opciones de un filtro. El valor "" significa "todas". */
export function FiltroDesplegable({ titulo, opciones, valor, alCambiar }: {
  titulo: string;
  opciones: Opcion[];
  valor: string;
  alCambiar: (valor: string) => void;
}) {
  const [abierto, setAbierto] = useState(false);
  const contenedor = useRef<HTMLDivElement>(null);
  const boton = useRef<HTMLButtonElement>(null);

  // Se cierra al pulsar fuera o con Escape, como cualquier menú
  useEffect(() => {
    if (!abierto) return;

    function alPulsar(evento: MouseEvent) {
      if (!contenedor.current?.contains(evento.target as Node)) setAbierto(false);
    }
    function alTeclear(evento: KeyboardEvent) {
      if (evento.key === "Escape") {
        setAbierto(false);
        boton.current?.focus();
      }
    }

    document.addEventListener("mousedown", alPulsar);
    document.addEventListener("keydown", alTeclear);
    return () => {
      document.removeEventListener("mousedown", alPulsar);
      document.removeEventListener("keydown", alTeclear);
    };
  }, [abierto]);

  const actual = opciones.find((opcion) => opcion.valor === valor);

  return (
    <div className="desplegable" ref={contenedor}>
      <button
        ref={boton}
        type="button"
        className={valor ? "desplegable-boton desplegable-activo" : "desplegable-boton"}
        aria-expanded={abierto}
        onClick={() => setAbierto(!abierto)}
      >
        {titulo}: {actual?.texto}
        <svg className={abierto ? "desplegable-flecha girada" : "desplegable-flecha"} aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {abierto && (
        <div className="desplegable-panel" role="group" aria-label={titulo}>
          {opciones.map((opcion) => (
            <button
              key={opcion.valor}
              type="button"
              className="desplegable-opcion"
              aria-pressed={opcion.valor === valor}
              autoFocus={opcion.valor === valor}
              onClick={() => {
                alCambiar(opcion.valor);
                setAbierto(false);
                boton.current?.focus();
              }}
            >
              {opcion.texto}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
