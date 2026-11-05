// Los montos llegan de la API como texto ("6765.86") y se tratan siempre como texto.
// Nunca se convierten a número: parseFloat introduce errores de redondeo con dinero.

/** "6765.86" -> "6.765,86" */
export function formatMonto(valor: string): string {
  const negativo = valor.startsWith("-");
  const [entero, decimales = ""] = valor.replace("-", "").split(".");
  const conPuntos = entero.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${negativo ? "−" : ""}${conPuntos},${decimales.padEnd(2, "0").slice(0, 2)}`;
}

export function esNegativo(valor: string): boolean {
  return valor.startsWith("-") && !/^-0*(\.0*)?$/.test(valor);
}

/** Como formatMonto, pero con signo: "9.00" -> "+9,00" y "0.00" -> "0,00". */
export function formatDiferencia(valor: string): string {
  const esCero = /^-?0*(\.0*)?$/.test(valor);
  if (esCero) return "0,00";
  return valor.startsWith("-") ? formatMonto(valor) : `+${formatMonto(valor)}`;
}

/**
 * Convierte lo que escribe la persona al formato de la API.
 * Acepta "1520", "1520,5" y "1.520,50". Devuelve null si no es un monto válido;
 * "1520.50" se rechaza porque aquí el punto separa miles y no decimales.
 */
export function normalizarMonto(texto: string): string | null {
  const limpio = texto.trim();
  const valido = /^(\d+|\d{1,3}(\.\d{3})+)(,\d{1,2})?$/.test(limpio);
  if (!valido) return null;
  const [entero, decimales = ""] = limpio.replace(/\./g, "").split(",");
  return `${entero}.${decimales.padEnd(2, "0")}`;
}

/** "2026-06-10" -> "10/06/2026". Se parte el texto para no correr el día por la zona horaria. */
export function formatFecha(iso: string): string {
  const [anio, mes, dia] = iso.slice(0, 10).split("-");
  return `${dia}/${mes}/${anio}`;
}

export function formatFechaHora(iso: string): string {
  return new Date(iso).toLocaleString("es-VE", { dateStyle: "short", timeStyle: "short" });
}

/** "Tomás Iriarte" -> "TI" */
export function iniciales(nombre: string): string {
  return nombre.split(" ").map((parte) => parte[0]).slice(0, 2).join("");
}

export interface CaracterComparado {
  caracter: string;
  cambia: boolean;
}

/**
 * Compara dos montos ya formateados, carácter por carácter, para resaltar los distintos.
 * Solo presenta los datos: quién decide que es una transposición es el backend.
 */
export function compararMontos(monto: string, otro: string): CaracterComparado[] {
  return [...monto].map((caracter, i) => ({ caracter, cambia: caracter !== otro[i] }));
}
