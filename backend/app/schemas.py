"""Formas de entrada y salida de la API (validación con Pydantic).

Definir explícitamente qué campos salen evita filtrar datos por accidente
(por ejemplo, nunca se devuelve password_hash porque no está aquí).
"""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


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
