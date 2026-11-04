"""Modelo relacional del portal.

Tres bloques:
  1. Organización de la VP de Finanzas (departamentos, cargos, colaboradores)
  2. Seguridad (roles, usuarios, permisos por módulo)
  3. Proceso de negocio: cierres de caja y alertas de anomalías

Reglas de normalización aplicadas:
  - El colaborador NO guarda su departamento: lo obtiene a través de su cargo.
    Si lo guardara en ambos lados, podrían quedar inconsistentes.
  - La diferencia de un cierre (declarado - sistema) NO se guarda: se calcula.
  - Quién gestionó una alerta NO se guarda en la alerta: sale del historial.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer,
    Numeric, String, Table, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


# Montos: NUMERIC(12,2), nunca float (0.1 + 0.2 != 0.3 en punto flotante)
Monto = Numeric(12, 2)


# =====================================================================
# 1. ORGANIZACIÓN
# =====================================================================
class Pais(Base):
    __tablename__ = "pais"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True)
    codigo_iso: Mapped[str] = mapped_column(String(2), unique=True)


class Departamento(Base):
    __tablename__ = "departamento"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str] = mapped_column(String(255))

    cargos: Mapped[list["Cargo"]] = relationship(back_populates="departamento")


class Nivel(Base):
    """Seniority como catálogo ordenado (no texto libre repetido)."""
    __tablename__ = "nivel"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), unique=True)
    orden: Mapped[int] = mapped_column(unique=True)


# Relación N:M — un cargo tiene varias funciones; una función puede
# repetirse en varios cargos (ej. "Elaborar reportes de gestión").
cargo_funcion = Table(
    "cargo_funcion",
    Base.metadata,
    Column("cargo_id", ForeignKey("cargo.id", ondelete="CASCADE"), primary_key=True),
    Column("funcion_id", ForeignKey("funcion.id", ondelete="RESTRICT"), primary_key=True),
)


class Funcion(Base):
    __tablename__ = "funcion"
    id: Mapped[int] = mapped_column(primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(200), unique=True)


class Cargo(Base):
    __tablename__ = "cargo"
    __table_args__ = (UniqueConstraint("nombre", "departamento_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"))
    nivel_id: Mapped[int] = mapped_column(ForeignKey("nivel.id"))

    departamento: Mapped[Departamento] = relationship(back_populates="cargos")
    nivel: Mapped[Nivel] = relationship()
    funciones: Mapped[list[Funcion]] = relationship(secondary=cargo_funcion)


class Colaborador(Base):
    __tablename__ = "colaborador"
    __table_args__ = (CheckConstraint("estado IN ('activo','inactivo')", name="ck_colaborador_estado"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    nombres: Mapped[str] = mapped_column(String(80))
    apellidos: Mapped[str] = mapped_column(String(80))
    correo: Mapped[str] = mapped_column(String(120), unique=True)
    pais_id: Mapped[int] = mapped_column(ForeignKey("pais.id"))
    fecha_ingreso: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(10), default="activo")
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargo.id"))

    pais: Mapped[Pais] = relationship()
    cargo: Mapped[Cargo] = relationship()

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    @property
    def departamento_id(self) -> int:
        return self.cargo.departamento_id


# =====================================================================
# 2. SEGURIDAD
# =====================================================================
class Rol(Base):
    __tablename__ = "rol"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)  # ADMIN | JEFE_DEPTO | COLABORADOR
    nombre: Mapped[str] = mapped_column(String(60))


class Usuario(Base):
    """Credenciales separadas de los datos de RR. HH. del colaborador."""
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    colaborador_id: Mapped[int] = mapped_column(ForeignKey("colaborador.id"), unique=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"))
    password_hash: Mapped[str] = mapped_column(String(100))  # bcrypt, nunca texto plano
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    colaborador: Mapped[Colaborador] = relationship()
    rol: Mapped[Rol] = relationship()


class Modulo(Base):
    __tablename__ = "modulo"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str] = mapped_column(String(255))
    orden: Mapped[int] = mapped_column(default=0)


class PermisoModulo(Base):
    """Qué rol, de qué departamento, accede a qué módulo y con qué nivel.

    departamento_id NULL = aplica a ese rol en cualquier departamento.
    El rol ADMIN no necesita filas: tiene acceso total por definición.
    """
    __tablename__ = "permiso_modulo"
    __table_args__ = (
        UniqueConstraint("modulo_id", "rol_id", "departamento_id"),
        CheckConstraint("nivel_acceso IN ('lectura','escritura')", name="ck_permiso_nivel"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    modulo_id: Mapped[int] = mapped_column(ForeignKey("modulo.id"))
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"))
    departamento_id: Mapped[int | None] = mapped_column(ForeignKey("departamento.id"))
    nivel_acceso: Mapped[str] = mapped_column(String(10))

    modulo: Mapped[Modulo] = relationship()


# =====================================================================
# 3. CIERRES DE CAJA Y ALERTAS
# =====================================================================
class Tienda(Base):
    __tablename__ = "tienda"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    pais_id: Mapped[int] = mapped_column(ForeignKey("pais.id"))

    pais: Mapped[Pais] = relationship()


class Cajero(Base):
    """Personal de Operación (tiendas), no de la VP de Finanzas."""
    __tablename__ = "cajero"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    tienda: Mapped[Tienda] = relationship()


class CierreCaja(Base):
    """Un cierre de turno: lo que el cajero declaró vs. lo que registró el sistema.

    tienda_id se guarda aunque el cajero ya tenga tienda: es la tienda donde
    ocurrió ESTE cierre (hecho histórico). Si mañana el cajero cambia de
    tienda, sus cierres pasados no deben moverse con él.
    """
    __tablename__ = "cierre_caja"
    __table_args__ = (
        CheckConstraint("monto_declarado >= 0", name="ck_cierre_declarado"),
        CheckConstraint("monto_sistema >= 0", name="ck_cierre_sistema"),
        CheckConstraint("origen IN ('carga_inicial','portal')", name="ck_cierre_origen"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id"))
    cajero_id: Mapped[int] = mapped_column(ForeignKey("cajero.id"), index=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    monto_declarado: Mapped[Decimal] = mapped_column(Monto)
    monto_sistema: Mapped[Decimal] = mapped_column(Monto)
    origen: Mapped[str] = mapped_column(String(15), default="portal")
    # NULL solo para la carga inicial del dataset
    registrado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)

    tienda: Mapped[Tienda] = relationship()
    cajero: Mapped[Cajero] = relationship()
    registrado_por: Mapped[Usuario | None] = relationship()
    alertas: Mapped[list["Alerta"]] = relationship(back_populates="cierre")

    @property
    def diferencia(self) -> Decimal:
        return self.monto_declarado - self.monto_sistema


REGLAS = ("FUERA_DE_RANGO", "TRANSPOSICION", "REINCIDENCIA", "DUPLICADO")
SEVERIDADES = ("baja", "media", "alta")
ESTADOS_ALERTA = ("pendiente", "revisada", "descartada")


class Alerta(Base):
    __tablename__ = "alerta"
    __table_args__ = (
        # Re-ejecutar la detección no duplica alertas
        UniqueConstraint("cierre_id", "regla", name="uq_alerta_cierre_regla"),
        CheckConstraint(f"regla IN {REGLAS}", name="ck_alerta_regla"),
        CheckConstraint(f"severidad IN {SEVERIDADES}", name="ck_alerta_severidad"),
        CheckConstraint(f"estado IN {ESTADOS_ALERTA}", name="ck_alerta_estado"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    cierre_id: Mapped[int] = mapped_column(ForeignKey("cierre_caja.id"), index=True)
    regla: Mapped[str] = mapped_column(String(20))
    severidad: Mapped[str] = mapped_column(String(5))
    detalle: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(10), default="pendiente", index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)

    cierre: Mapped[CierreCaja] = relationship(back_populates="alertas")
    historial: Mapped[list["AlertaHistorial"]] = relationship(
        back_populates="alerta", order_by="AlertaHistorial.id"
    )


class AlertaHistorial(Base):
    """Bitácora de solo inserción: cada cambio de estado de una alerta.

    Nunca se actualiza ni se borra una fila. usuario_id NULL = acción del
    sistema (la detección automática que crea la alerta).
    """
    __tablename__ = "alerta_historial"
    id: Mapped[int] = mapped_column(primary_key=True)
    alerta_id: Mapped[int] = mapped_column(ForeignKey("alerta.id"), index=True)
    estado_anterior: Mapped[str | None] = mapped_column(String(10))
    estado_nuevo: Mapped[str] = mapped_column(String(10))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    comentario: Mapped[str] = mapped_column(String(500))

    alerta: Mapped[Alerta] = relationship(back_populates="historial")
    usuario: Mapped[Usuario | None] = relationship()


class ParametroDeteccion(Base):
    """Umbrales de las reglas, en la BD y no fijos en el código."""
    __tablename__ = "parametro_deteccion"
    clave: Mapped[str] = mapped_column(String(40), primary_key=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    descripcion: Mapped[str] = mapped_column(String(255))
