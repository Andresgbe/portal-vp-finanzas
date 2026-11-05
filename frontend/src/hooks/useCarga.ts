import { useCallback, useEffect, useState } from "react";
import { ErrorApi } from "../api/cliente";

/** Carga datos de la API y expone los tres estados de toda pantalla: cargando, error y datos. */
export function useCarga<T>(cargar: () => Promise<T>, dependencias: unknown[]) {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    // Si cambian los filtros antes de que llegue la respuesta, se ignora la respuesta vieja
    let vigente = true;
    setCargando(true);
    setError(null);

    cargar()
      .then((resultado) => {
        if (vigente) setDatos(resultado);
      })
      .catch((e: ErrorApi) => {
        if (vigente) setError(e.message);
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...dependencias, version]);

  const recargar = useCallback(() => setVersion((v) => v + 1), []);

  return { datos, setDatos, error, cargando, recargar };
}
