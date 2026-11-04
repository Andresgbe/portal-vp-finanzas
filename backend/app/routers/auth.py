"""Login, logout y datos de la sesión actual."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import UsuarioActual, permisos_de, usuario_actual
from ..models import Colaborador, Modulo, Usuario
from ..schemas import LoginIn, ModuloOut, SesionOut
from ..security import COOKIE_SESION, HASH_SEÑUELO, crear_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["autenticación"])

MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 15
CREDENCIALES_INVALIDAS = "Correo o contraseña incorrectos"


def _como_utc(dt: datetime) -> datetime:
    # SQLite devuelve fechas sin zona horaria; las tratamos como UTC
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.post("/login", response_model=SesionOut)
def login(datos: LoginIn, response: Response, db: Session = Depends(get_db)):
    ahora = datetime.now(timezone.utc)
    usuario = db.scalar(
        select(Usuario).join(Colaborador)
        .where(func.lower(Colaborador.correo) == datos.correo.strip().lower())
    )

    if usuario is None:
        # Se verifica contra un hash señuelo para tardar lo mismo que con un
        # correo real: así no se puede adivinar qué correos existen.
        verify_password(datos.password, HASH_SEÑUELO)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, CREDENCIALES_INVALIDAS)

    if usuario.bloqueado_hasta and _como_utc(usuario.bloqueado_hasta) > ahora:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            f"Demasiados intentos fallidos. Intenta de nuevo en {MINUTOS_BLOQUEO} minutos.")

    if not verify_password(datos.password, usuario.password_hash):
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= MAX_INTENTOS:
            usuario.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
            usuario.intentos_fallidos = 0
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, CREDENCIALES_INVALIDAS)

    # Contraseña correcta pero usuario o colaborador inactivo: mismo mensaje genérico
    if not usuario.activo or usuario.colaborador.estado != "activo":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, CREDENCIALES_INVALIDAS)

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_acceso = ahora
    db.commit()

    response.set_cookie(
        COOKIE_SESION,
        crear_token(usuario.id),
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,      # JavaScript no puede leerla (protege contra XSS)
        samesite="strict",  # el navegador no la envía desde otros sitios (protege contra CSRF)
        secure=settings.cookie_secure,  # solo por HTTPS en producción
        path="/",
    )
    return _sesion(db, usuario_actual_desde(usuario))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_SESION, path="/", samesite="strict",
                           secure=settings.cookie_secure, httponly=True)


@router.get("/me", response_model=SesionOut)
def me(actual: UsuarioActual = Depends(usuario_actual), db: Session = Depends(get_db)):
    return _sesion(db, actual)


def usuario_actual_desde(usuario: Usuario) -> UsuarioActual:
    return UsuarioActual(usuario, usuario.rol.codigo, usuario.colaborador.cargo.departamento_id)


def _sesion(db: Session, actual: UsuarioActual) -> SesionOut:
    permisos = permisos_de(db, actual)
    modulos = db.scalars(select(Modulo).where(Modulo.codigo.in_(permisos)).order_by(Modulo.orden))
    colab = actual.usuario.colaborador
    return SesionOut(
        usuario_id=actual.id,
        colaborador_id=colab.id,
        nombre=colab.nombre_completo,
        correo=colab.correo,
        rol=actual.rol,
        departamento_id=actual.departamento_id,
        departamento=colab.cargo.departamento.nombre,
        modulos=[ModuloOut(codigo=m.codigo, nombre=m.nombre, descripcion=m.descripcion,
                           nivel_acceso=permisos[m.codigo]) for m in modulos],
    )
