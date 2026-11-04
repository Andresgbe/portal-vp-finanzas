"""Control de acceso. TODA autorización del portal pasa por aquí.

Tres preguntas, en este orden, antes de responder cualquier endpoint:
  1. ¿Quién eres?            -> usuario_actual   (401 si no hay sesión válida)
  2. ¿Puedes usar el módulo? -> requiere_modulo  (403 si tu rol/depto no tiene permiso)
  3. ¿Es de tu alcance?      -> verificar_departamento (403 si es de otro departamento)

Ocultar botones en el frontend es solo comodidad visual; la seguridad
real está en estas funciones.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Cargo, Colaborador, Modulo, PermisoModulo, Usuario
from .security import COOKIE_SESION, leer_token

ADMIN, JEFE, COLABORADOR = "ADMIN", "JEFE_DEPTO", "COLABORADOR"
NIVELES = {"lectura": 1, "escritura": 2}


@dataclass
class UsuarioActual:
    usuario: Usuario
    rol: str
    departamento_id: int

    @property
    def id(self) -> int:
        return self.usuario.id

    @property
    def es_admin(self) -> bool:
        return self.rol == ADMIN


def _no_autenticado() -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión inválida o expirada")


def usuario_actual(request: Request, db: Session = Depends(get_db)) -> UsuarioActual:
    token = request.cookies.get(COOKIE_SESION)
    usuario_id = leer_token(token) if token else None
    if usuario_id is None:
        raise _no_autenticado()

    usuario = db.scalar(
        select(Usuario)
        .options(joinedload(Usuario.rol),
                 joinedload(Usuario.colaborador).joinedload(Colaborador.cargo))
        .where(Usuario.id == usuario_id)
    )
    # Se revisa en cada request: desactivar a alguien corta su acceso al instante
    if not usuario or not usuario.activo or usuario.colaborador.estado != "activo":
        raise _no_autenticado()

    return UsuarioActual(usuario, usuario.rol.codigo, usuario.colaborador.cargo.departamento_id)


def permisos_de(db: Session, actual: UsuarioActual) -> dict[str, str]:
    """{codigo_modulo: 'lectura' | 'escritura'} para el usuario."""
    if actual.es_admin:
        return {m.codigo: "escritura" for m in db.scalars(select(Modulo))}

    filas = db.execute(
        select(Modulo.codigo, PermisoModulo.nivel_acceso)
        .join(PermisoModulo, PermisoModulo.modulo_id == Modulo.id)
        .where(PermisoModulo.rol_id == actual.usuario.rol_id)
        .where(or_(PermisoModulo.departamento_id.is_(None),
                   PermisoModulo.departamento_id == actual.departamento_id))
    ).all()
    permisos: dict[str, str] = {}
    for codigo, nivel in filas:
        if NIVELES[nivel] > NIVELES.get(permisos.get(codigo, ""), 0):
            permisos[codigo] = nivel
    return permisos


def requiere_modulo(codigo: str, nivel: str = "lectura"):
    """Fábrica de dependencias: Depends(requiere_modulo("CIERRES", "escritura"))."""
    def _dep(actual: UsuarioActual = Depends(usuario_actual),
             db: Session = Depends(get_db)) -> UsuarioActual:
        tiene = permisos_de(db, actual).get(codigo)
        if not tiene or NIVELES[tiene] < NIVELES[nivel]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes acceso a este módulo")
        return actual
    return _dep


def verificar_departamento(actual: UsuarioActual, departamento_id: int) -> None:
    """Admin ve todo; los demás solo su propio departamento."""
    if not actual.es_admin and actual.departamento_id != departamento_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes acceso a otro departamento")


def departamento_de_colaborador(db: Session, colaborador_id: int) -> int | None:
    return db.scalar(
        select(Cargo.departamento_id).join(Colaborador, Colaborador.cargo_id == Cargo.id)
        .where(Colaborador.id == colaborador_id)
    )
