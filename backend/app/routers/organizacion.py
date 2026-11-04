"""Módulos de consulta de la estructura organizacional (módulos "dummy").

Aunque no tienen lógica de negocio compleja, sí aplican control de acceso
completo: rol + módulo + departamento en cada endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..database import get_db
from ..deps import (COLABORADOR, UsuarioActual, departamento_de_colaborador,
                    requiere_modulo, verificar_departamento)
from ..models import Cargo, Colaborador, Departamento, Nivel
from ..schemas import (CargoEstructura, ColaboradorBasico, ColaboradorDetalle,
                       DepartamentoOut, DepartamentoResumen, EstructuraOut,
                       FichaColaborador)

router = APIRouter(prefix="/api", tags=["organización"])

_CARGA_COLABORADOR = (
    joinedload(Colaborador.pais),
    joinedload(Colaborador.cargo).joinedload(Cargo.nivel),
    joinedload(Colaborador.cargo).joinedload(Cargo.departamento),
    joinedload(Colaborador.cargo).selectinload(Cargo.funciones),
)


def _detalle(c: Colaborador) -> dict:
    return dict(
        id=c.id, nombre=c.nombre_completo, cargo=c.cargo.nombre, correo=c.correo,
        nivel=c.cargo.nivel.nombre, departamento=c.cargo.departamento.nombre,
        pais=c.pais.nombre, fecha_ingreso=c.fecha_ingreso, estado=c.estado,
    )


def _ficha(c: Colaborador) -> FichaColaborador:
    return FichaColaborador(**_detalle(c), funciones=[f.descripcion for f in c.cargo.funciones])


def _cargar_colaborador(db: Session, colaborador_id: int) -> Colaborador | None:
    return db.scalar(select(Colaborador).options(*_CARGA_COLABORADOR)
                     .where(Colaborador.id == colaborador_id))


# ---------------------------------------------------------------- Mi perfil
@router.get("/perfil", response_model=FichaColaborador)
def mi_perfil(actual: UsuarioActual = Depends(requiere_modulo("MI_PERFIL")),
              db: Session = Depends(get_db)):
    return _ficha(_cargar_colaborador(db, actual.usuario.colaborador_id))


# ---------------------------------------------------------------- Directorio
@router.get("/departamentos", response_model=list[DepartamentoResumen])
def listar_departamentos(actual: UsuarioActual = Depends(requiere_modulo("DIRECTORIO")),
                         db: Session = Depends(get_db)):
    consulta = (
        select(Departamento,
               func.count(Colaborador.id),
               func.count(Colaborador.id).filter(Colaborador.estado == "activo"))
        .outerjoin(Cargo, Cargo.departamento_id == Departamento.id)
        .outerjoin(Colaborador, Colaborador.cargo_id == Cargo.id)
        .group_by(Departamento.id).order_by(Departamento.nombre)
    )
    if not actual.es_admin:
        consulta = consulta.where(Departamento.id == actual.departamento_id)
    return [DepartamentoResumen(id=d.id, nombre=d.nombre, descripcion=d.descripcion,
                                total_colaboradores=total, activos=activos)
            for d, total, activos in db.execute(consulta)]


@router.get("/departamentos/{departamento_id}/colaboradores",
            response_model=list[ColaboradorDetalle | ColaboradorBasico])
def colaboradores_del_departamento(
    departamento_id: int,
    actual: UsuarioActual = Depends(requiere_modulo("DIRECTORIO")),
    db: Session = Depends(get_db),
):
    verificar_departamento(actual, departamento_id)
    consulta = (select(Colaborador).options(*_CARGA_COLABORADOR)
                .join(Cargo).join(Nivel).where(Cargo.departamento_id == departamento_id)
                .order_by(Nivel.orden.desc(), Colaborador.apellidos))

    if actual.rol == COLABORADOR:
        # Información limitada: solo compañeros activos y solo datos de contacto
        consulta = consulta.where(Colaborador.estado == "activo")
        return [ColaboradorBasico(id=c.id, nombre=c.nombre_completo, cargo=c.cargo.nombre,
                                  correo=c.correo) for c in db.scalars(consulta)]
    return [ColaboradorDetalle(**_detalle(c)) for c in db.scalars(consulta)]


@router.get("/colaboradores/{colaborador_id}", response_model=FichaColaborador)
def ficha_colaborador(colaborador_id: int,
                      actual: UsuarioActual = Depends(requiere_modulo("DIRECTORIO")),
                      db: Session = Depends(get_db)):
    depto = departamento_de_colaborador(db, colaborador_id)
    if depto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Colaborador no encontrado")

    es_uno_mismo = colaborador_id == actual.usuario.colaborador_id
    if actual.rol == COLABORADOR and not es_uno_mismo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo puedes ver tu propia ficha")
    verificar_departamento(actual, depto)
    return _ficha(_cargar_colaborador(db, colaborador_id))


# ---------------------------------------------------------------- Estructura
@router.get("/departamentos/{departamento_id}/estructura", response_model=EstructuraOut)
def estructura_departamento(departamento_id: int,
                            actual: UsuarioActual = Depends(requiere_modulo("ESTRUCTURA")),
                            db: Session = Depends(get_db)):
    verificar_departamento(actual, departamento_id)
    depto = db.get(Departamento, departamento_id)
    if depto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Departamento no encontrado")

    ocupantes = dict(db.execute(
        select(Colaborador.cargo_id, func.count()).where(Colaborador.estado == "activo")
        .group_by(Colaborador.cargo_id)
    ).all())
    cargos = db.scalars(
        select(Cargo).options(joinedload(Cargo.nivel), selectinload(Cargo.funciones))
        .join(Nivel).where(Cargo.departamento_id == departamento_id).order_by(Nivel.orden.desc())
    )
    return EstructuraOut(
        departamento=DepartamentoOut.model_validate(depto),
        cargos=[CargoEstructura(
            id=c.id, nombre=c.nombre, nivel=c.nivel.nombre, nivel_orden=c.nivel.orden,
            departamento=depto.nombre, funciones=[f.descripcion for f in c.funciones],
            ocupantes=ocupantes.get(c.id, 0),
        ) for c in cargos],
    )
