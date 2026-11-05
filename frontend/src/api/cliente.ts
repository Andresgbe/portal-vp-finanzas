// Único punto del frontend que llama a fetch: el manejo de errores queda en un solo lugar.
//
// El token de sesión NUNCA se toca aquí. Vive en una cookie httpOnly que JavaScript
// no puede leer, y el navegador la envía solo gracias a credentials: "same-origin".

export class ErrorApi extends Error {
  status: number;

  constructor(mensaje: string, status: number) {
    super(mensaje);
    this.status = status;
  }
}

const MENSAJES_POR_ESTADO: Record<number, string> = {
  401: "Tu sesión expiró. Vuelve a iniciar sesión.",
  403: "No tienes permiso para ver esto.",
  404: "No encontramos lo que buscas.",
};
const MENSAJE_GENERICO = "Ocurrió un error inesperado. Intenta de nuevo.";

let alExpirar: (() => void) | null = null;

/** El contexto de sesión se registra aquí para enterarse de que la sesión expiró. */
export function registrarAlExpirarSesion(funcion: () => void) {
  alExpirar = funcion;
}

async function leerMensaje(respuesta: Response): Promise<string> {
  try {
    const cuerpo = await respuesta.json();
    if (typeof cuerpo.detail === "string") return cuerpo.detail;
  } catch {
    // Un error 500 puede no traer JSON: se usa el mensaje genérico
  }
  return MENSAJES_POR_ESTADO[respuesta.status] ?? MENSAJE_GENERICO;
}

/** Descarga un archivo de la API. Los permisos los valida el backend, igual que en cualquier consulta. */
export async function descargar(ruta: string, nombreArchivo: string): Promise<void> {
  let respuesta: Response;
  try {
    respuesta = await fetch(`/api${ruta}`, { credentials: "same-origin" });
  } catch {
    throw new ErrorApi("No se pudo conectar con el servidor.", 0);
  }

  if (!respuesta.ok) {
    if (respuesta.status === 401) alExpirar?.();
    throw new ErrorApi(await leerMensaje(respuesta), respuesta.status);
  }

  const enlace = document.createElement("a");
  enlace.href = URL.createObjectURL(await respuesta.blob());
  enlace.download = nombreArchivo;
  enlace.click();
  URL.revokeObjectURL(enlace.href);
}

export async function api<T>(ruta: string, cuerpo?: unknown, metodo?: string): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(`/api${ruta}`, {
      method: metodo ?? (cuerpo === undefined ? "GET" : "POST"),
      credentials: "same-origin",
      headers: cuerpo === undefined ? undefined : { "Content-Type": "application/json" },
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    });
  } catch {
    throw new ErrorApi("No se pudo conectar con el servidor.", 0);
  }

  if (!respuesta.ok) {
    // En /auth/* un 401 es normal (clave errada o sin sesión): lo decide quien llama.
    // En cualquier otra ruta significa que la sesión expiró y hay que volver al login.
    if (respuesta.status === 401 && !ruta.startsWith("/auth/")) alExpirar?.();
    throw new ErrorApi(await leerMensaje(respuesta), respuesta.status);
  }

  if (respuesta.status === 204) return undefined as T;
  return respuesta.json() as Promise<T>;
}
