// Qué pantalla corresponde a cada módulo. Qué módulos ve cada persona lo decide
// el backend en /auth/me; aquí no se decide ningún permiso.
export const RUTA_DE_MODULO: Record<string, string> = {
  MI_PERFIL: "/perfil",
  DIRECTORIO: "/directorio",
  ESTRUCTURA: "/estructura",
  CIERRES: "/cierres",
  ALERTAS: "/alertas",
};
