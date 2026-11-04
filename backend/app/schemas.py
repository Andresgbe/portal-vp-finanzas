"""Formas de entrada y salida de la API (validación con Pydantic).

Definir explícitamente qué campos salen evita filtrar datos por accidente
(por ejemplo, nunca se devuelve password_hash porque no está aquí).
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

# Todas las fechas-hora se guardan en UTC. SQLite las devuelve "sin zona";
# aquí se marcan como UTC para que el frontend las convierta bien a hora local.
FechaUTC = Annotated[datetime, AfterValidator(lambda d: d if d.tzinfo else d.replace(tzinfo=timezone.utc))]


class Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Autenticación ----------
class LoginIn(BaseModel):
    correo: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class ModuloOut(BaseModel):
    codigo: str
    nombre: str
    descripcion: str
    nivel_acceso: str


class SesionOut(BaseModel):
    usuario_id: int
    colaborador_id: int
    nombre: str
    correo: str
    rol: str
    departamento_id: int
    departamento: str
    modulos: list[ModuloOut]


# ---------- Organización ----------
class DepartamentoOut(Orm):
    id: int
    nombre: str
    descripcion: str


class DepartamentoResumen(DepartamentoOut):
    total_colaboradores: int
    activos: int


class FuncionOut(Orm):
    id: int
    descripcion: str


class CargoOut(BaseModel):
    id: int
    nombre: str
    nivel: str
    nivel_orden: int
    departamento: str
    funciones: list[str]


class ColaboradorBasico(BaseModel):
    """Vista limitada (rol Colaborador viendo a sus compañeros)."""
    id: int
    nombre: str
    cargo: str
    correo: str


class ColaboradorDetalle(ColaboradorBasico):
    """Vista completa (Jefe de su departamento o Admin, o uno mismo)."""
    nivel: str
    departamento: str
    pais: str
    fecha_ingreso: date
    estado: str


class FichaColaborador(ColaboradorDetalle):
    funciones: list[str]


class CargoEstructura(CargoOut):
    ocupantes: int


class EstructuraOut(BaseModel):
    departamento: DepartamentoOut
    cargos: list[CargoEstructura]


# ---------- Cierres de caja ----------
class TiendaOut(BaseModel):
    id: int
    nombre: str
    pais: str


class CajeroOut(BaseModel):
    id: int
    nombre: str
    tienda_id: int
    tienda: str


class CierreIn(BaseModel):
    tienda_id: int
    cajero_id: int
    fecha: date
    monto_declarado: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    monto_sistema: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class AlertaResumen(BaseModel):
    id: int
    regla: str
    severidad: str
    estado: str


class CierreOut(BaseModel):
    id: int
    fecha: date
    tienda_id: int
    tienda: str
    cajero_id: int
    cajero: str
    monto_declarado: Decimal
    monto_sistema: Decimal
    diferencia: Decimal
    origen: str
    registrado_por: str | None
    registrado_en: FechaUTC
    alertas: list[AlertaResumen]


class CierreCreado(CierreOut):
    alertas_generadas: int


# ---------- Alertas ----------
class HistorialOut(BaseModel):
    fecha: FechaUTC
    estado_anterior: str | None
    estado_nuevo: str
    usuario: str
    comentario: str


class AlertaOut(BaseModel):
    id: int
    regla: str
    severidad: str
    estado: str
    detalle: str
    creada_en: FechaUTC
    cierre_id: int
    fecha_cierre: date
    tienda: str
    cajero_id: int
    cajero: str
    monto_declarado: Decimal
    monto_sistema: Decimal
    diferencia: Decimal
    gestionada_por: str | None
    gestionada_en: FechaUTC | None
    puede_gestionar: bool
    motivo_no_gestionable: str | None


class AlertaDetalle(AlertaOut):
    historial: list[HistorialOut]


class GestionIn(BaseModel):
    estado: Literal["revisada", "descartada"]
    comentario: str = Field(min_length=10, max_length=500)


class ConteoOut(BaseModel):
    clave: str
    total: int


class CajeroRiesgo(BaseModel):
    cajero_id: int
    cajero: str
    tienda: str
    alertas_abiertas: int


class ResumenAlertas(BaseModel):
    por_estado: list[ConteoOut]
    por_regla: list[ConteoOut]
    por_severidad_pendientes: list[ConteoOut]
    cajeros_con_mas_alertas: list[CajeroRiesgo]


class ParametroOut(BaseModel):
    clave: str
    valor: Decimal
    descripcion: str
