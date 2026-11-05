// Forma de las respuestas de la API (ver backend/app/schemas.py).
// Los montos son string a propósito: nunca se convierten a número en el cliente.

export type NivelAcceso = "lectura" | "escritura";

export interface Modulo {
  codigo: string;
  nombre: string;
  descripcion: string;
  nivel_acceso: NivelAcceso;
}

export interface Sesion {
  usuario_id: number;
  colaborador_id: number;
  nombre: string;
  correo: string;
  rol: "ADMIN" | "JEFE_DEPTO" | "COLABORADOR";
  departamento_id: number;
  departamento: string;
  modulos: Modulo[];
}

// ---------- Organización ----------
export interface DepartamentoResumen {
  id: number;
  nombre: string;
  descripcion: string;
  total_colaboradores: number;
  activos: number;
}

export interface ColaboradorBasico {
  id: number;
  nombre: string;
  cargo: string;
  correo: string;
}

/** El rol Colaborador solo recibe la vista básica: el resto de campos puede no venir. */
export interface Colaborador extends ColaboradorBasico {
  nivel?: string;
  departamento?: string;
  pais?: string;
  fecha_ingreso?: string;
  estado?: string;
}

export interface FichaColaborador extends ColaboradorBasico {
  nivel: string;
  departamento: string;
  pais: string;
  fecha_ingreso: string;
  estado: string;
  funciones: string[];
}

export interface CargoEstructura {
  id: number;
  nombre: string;
  nivel: string;
  nivel_orden: number;
  departamento: string;
  funciones: string[];
  ocupantes: number;
}

export interface Estructura {
  departamento: { id: number; nombre: string; descripcion: string };
  cargos: CargoEstructura[];
}

// ---------- Cierres ----------
export interface Tienda {
  id: number;
  nombre: string;
  pais: string;
}

export interface Cajero {
  id: number;
  nombre: string;
  tienda_id: number;
  tienda: string;
}

export interface Cierre {
  id: number;
  fecha: string;
  tienda_id: number;
  tienda: string;
  cajero_id: number;
  cajero: string;
  monto_declarado: string;
  monto_sistema: string;
  diferencia: string;
  origen: string;
  registrado_por: string | null;
  registrado_en: string;
  alertas: { id: number; regla: string; severidad: string; estado: string }[];
  estado: "activo" | "inhabilitado";
  inhabilitado_por: string | null;
  inhabilitado_en: string | null;
  motivo_inhabilitacion: string | null;
  /** Lo decide el backend según la tabla permiso_accion */
  puede_inhabilitar: boolean;
}

export interface CierreCreado extends Cierre {
  alertas_generadas: number;
}

// ---------- Alertas ----------
export interface Alerta {
  id: number;
  regla: string;
  severidad: string;
  estado: string;
  detalle: string;
  creada_en: string;
  cierre_id: number;
  fecha_cierre: string;
  tienda: string;
  cajero_id: number;
  cajero: string;
  monto_declarado: string;
  monto_sistema: string;
  diferencia: string;
  gestionada_por: string | null;
  gestionada_en: string | null;
  puede_gestionar: boolean;
  motivo_no_gestionable: string | null;
}

export interface Historial {
  fecha: string;
  estado_anterior: string | null;
  estado_nuevo: string;
  usuario: string;
  comentario: string;
}

export interface AlertaDetalle extends Alerta {
  historial: Historial[];
}

export interface Conteo {
  clave: string;
  total: number;
}

export interface ResumenAlertas {
  por_estado: Conteo[];
  por_regla: Conteo[];
  por_severidad_pendientes: Conteo[];
  cajeros_con_mas_alertas: { cajero_id: number; cajero: string; tienda: string; alertas_abiertas: number }[];
}
