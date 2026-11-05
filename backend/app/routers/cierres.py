"""Proceso de negocio: cierres de caja y gestión de alertas de anomalías.

Segregación de funciones (control interno):
  - Tesorería REGISTRA cierres            (módulo CIERRES, escritura)
  - Contraloría GESTIONA las alertas       (módulo ALERTAS, escritura)
  - Nadie puede gestionar alertas de un cierre que registró él mismo,
    ni siquiera el Administrador.
  - Quién puede inhabilitar un cierre se define en la tabla permiso_accion.
    Quien lo registró tampoco puede: así no se esconde un faltante propio.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, func, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from ..database import get_db
from ..deps import UsuarioActual, permisos_de, requiere_accion, requiere_modulo, tiene_accion
from ..deteccion import detectar, reprocesar_todo
from ..models import (Alerta, AlertaHistorial, Cajero, CierreCaja, CierreHistorial,
                      ParametroDeteccion, Tienda, Usuario)
from ..reporte import generar_pdf_cierres
from ..schemas import (AlertaDetalle, AlertaOut, AlertaResumen, CajeroOut, CajeroRiesgo,
                       CierreCreado, CierreIn, CierreOut, ConteoOut, GestionIn,
                       HistorialOut, InhabilitarIn, ParametroOut, ResumenAlertas, TiendaOut)

router = APIRouter(prefix="/api", tags=["cierres y alertas"])

INHABILITAR_CIERRE = "INHABILITAR_CIERRE"

_CARGA_CIERRE = (
    joinedload(CierreCaja.tienda), joinedload(CierreCaja.cajero),
    joinedload(CierreCaja.registrado_por).joinedload(Usuario.colaborador),
    selectinload(CierreCaja.alertas),
    selectinload(CierreCaja.historial).joinedload(CierreHistorial.usuario).joinedload(Usuario.colaborador),
)
_CARGA_ALERTA = (
    joinedload(Alerta.cierre).joinedload(CierreCaja.tienda),
    joinedload(Alerta.cierre).joinedload(CierreCaja.cajero),
    selectinload(Alerta.historial).joinedload(AlertaHistorial.usuario).joinedload(Usuario.colaborador),
)


def _nombre_usuario(u: Usuario | None) -> str:
    return u.colaborador.nombre_completo if u else "Sistema"


def _cierre_out(c: CierreCaja, actual: UsuarioActual, tiene_permiso: bool) -> dict:
    # Quién lo inhabilitó sale del historial: no se duplica en la tabla cierre_caja
    baja = c.historial[-1] if c.estado == "inhabilitado" and c.historial else None
    return dict(
        id=c.id, fecha=c.fecha, tienda_id=c.tienda_id, tienda=c.tienda.nombre,
        cajero_id=c.cajero_id, cajero=c.cajero.nombre,
        monto_declarado=c.monto_declarado, monto_sistema=c.monto_sistema,
        diferencia=c.diferencia, origen=c.origen,
        registrado_por=_nombre_usuario(c.registrado_por) if c.registrado_por_id else "Carga inicial",
        registrado_en=c.registrado_en,
        alertas=[AlertaResumen(id=a.id, regla=a.regla, severidad=a.severidad, estado=a.estado)
                 for a in c.alertas],
        estado=c.estado,
        inhabilitado_por=_nombre_usuario(baja.usuario) if baja else None,
        inhabilitado_en=baja.fecha if baja else None,
        motivo_inhabilitacion=baja.motivo if baja else None,
        puede_inhabilitar=(tiene_permiso and c.estado == "activo"
                           and c.registrado_por_id != actual.id),
    )


def _registro_el_cierre(a: Alerta, actual: UsuarioActual) -> bool:
    """Segregación de funciones: un solo lugar decide si esta persona registró el cierre.
    Lo usan la pantalla (puede_gestionar) y el endpoint, para que nunca se contradigan."""
    return a.cierre.registrado_por_id == actual.id


def _motivo_no_gestionable(a: Alerta, actual: UsuarioActual, puede_escribir: bool) -> str | None:
    if not puede_escribir:
        return "Tu rol solo tiene acceso de lectura a las alertas."
    if a.estado != "pendiente":
        return "La alerta ya fue gestionada."
    if _registro_el_cierre(a, actual):
        return "Registraste este cierre: otra persona debe revisar sus alertas."
    return None


def _alerta_out(a: Alerta, actual: UsuarioActual, puede_escribir: bool, con_historial=False):
    # Quién gestionó la alerta se obtiene del historial (no se duplica en la tabla alerta)
    gestion = next((h for h in reversed(a.historial) if h.usuario_id is not None), None)
    motivo = _motivo_no_gestionable(a, actual, puede_escribir)
    c = a.cierre
    datos = dict(
        id=a.id, regla=a.regla, severidad=a.severidad, estado=a.estado, detalle=a.detalle,
        creada_en=a.creada_en, cierre_id=c.id, fecha_cierre=c.fecha, tienda=c.tienda.nombre,
        cajero_id=c.cajero_id, cajero=c.cajero.nombre, monto_declarado=c.monto_declarado,
        monto_sistema=c.monto_sistema, diferencia=c.diferencia,
        gestionada_por=_nombre_usuario(gestion.usuario) if gestion else None,
        gestionada_en=gestion.fecha if gestion else None,
        puede_gestionar=motivo is None, motivo_no_gestionable=motivo,
    )
    if con_historial:
        return AlertaDetalle(**datos, historial=[
            HistorialOut(fecha=h.fecha, estado_anterior=h.estado_anterior, estado_nuevo=h.estado_nuevo,
                         usuario=_nombre_usuario(h.usuario), comentario=h.comentario)
            for h in a.historial])
    return AlertaOut(**datos)


# ================================================================ Catálogos
@router.get("/tiendas", response_model=list[TiendaOut])
def tiendas(_: UsuarioActual = Depends(requiere_modulo("CIERRES")), db: Session = Depends(get_db)):
    return [TiendaOut(id=t.id, nombre=t.nombre, pais=t.pais.nombre)
            for t in db.scalars(select(Tienda).options(joinedload(Tienda.pais)).order_by(Tienda.nombre))]


@router.get("/cajeros", response_model=list[CajeroOut])
def cajeros(tienda_id: int | None = None,
            _: UsuarioActual = Depends(requiere_modulo("CIERRES")), db: Session = Depends(get_db)):
    q = select(Cajero).options(joinedload(Cajero.tienda)).where(Cajero.activo).order_by(Cajero.nombre)
    if tienda_id:
        q = q.where(Cajero.tienda_id == tienda_id)
    return [CajeroOut(id=c.id, nombre=c.nombre, tienda_id=c.tienda_id, tienda=c.tienda.nombre)
            for c in db.scalars(q)]


# ================================================================ Cierres
def _consulta_cierres(tienda_id: int | None, cajero_id: int | None, desde: date | None,
                      hasta: date | None, solo_con_alertas: bool):
    """La misma consulta para la tabla y el PDF: el reporte siempre coincide con la pantalla."""
    q = select(CierreCaja).options(*_CARGA_CIERRE).order_by(CierreCaja.fecha.desc(), CierreCaja.id.desc())
    if tienda_id:
        q = q.where(CierreCaja.tienda_id == tienda_id)
    if cajero_id:
        q = q.where(CierreCaja.cajero_id == cajero_id)
    if desde:
        q = q.where(CierreCaja.fecha >= desde)
    if hasta:
        q = q.where(CierreCaja.fecha <= hasta)
    if solo_con_alertas:
        q = q.where(CierreCaja.alertas.any())
    return q


@router.get("/cierres", response_model=list[CierreOut])
def listar_cierres(
    tienda_id: int | None = None, cajero_id: int | None = None,
    desde: date | None = None, hasta: date | None = None,
    solo_con_alertas: bool = False,
    actual: UsuarioActual = Depends(requiere_modulo("CIERRES")), db: Session = Depends(get_db),
):
    q = _consulta_cierres(tienda_id, cajero_id, desde, hasta, solo_con_alertas)
    permiso = tiene_accion(db, actual, INHABILITAR_CIERRE)
    return [CierreOut(**_cierre_out(c, actual, permiso)) for c in db.scalars(q)]


@router.get("/cierres/reporte.pdf")
def reporte_cierres(
    tienda_id: int | None = None, cajero_id: int | None = None,
    desde: date | None = None, hasta: date | None = None,
    solo_con_alertas: bool = False,
    actual: UsuarioActual = Depends(requiere_modulo("CIERRES")), db: Session = Depends(get_db),
):
    """Reporte en PDF con los mismos permisos y filtros que la tabla."""
    cierres = list(db.scalars(_consulta_cierres(tienda_id, cajero_id, desde, hasta, solo_con_alertas)))

    filtros = []
    if tienda_id:
        tienda = db.get(Tienda, tienda_id)
        filtros.append(f"tienda {tienda.nombre if tienda else tienda_id}")
    if desde:
        filtros.append(f"desde {desde:%d/%m/%Y}")
    if hasta:
        filtros.append(f"hasta {hasta:%d/%m/%Y}")
    if solo_con_alertas:
        filtros.append("solo con alertas")

    contenido = generar_pdf_cierres(cierres, actual.usuario.colaborador.nombre_completo,
                                    ", ".join(filtros) or "ninguno")
    return Response(contenido, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="reporte-cierres.pdf"'})


@router.post("/cierres", response_model=CierreCreado, status_code=status.HTTP_201_CREATED)
def registrar_cierre(datos: CierreIn,
                     actual: UsuarioActual = Depends(requiere_modulo("CIERRES", "escritura")),
                     db: Session = Depends(get_db)):
    if datos.fecha > date.today():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La fecha del cierre no puede ser futura")
    cajero = db.get(Cajero, datos.cajero_id)
    if cajero is None or not cajero.activo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El cajero no existe o está inactivo")
    if cajero.tienda_id != datos.tienda_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El cajero no pertenece a esa tienda")

    cierre = CierreCaja(**datos.model_dump(), origen="portal", registrado_por_id=actual.id)
    db.add(cierre)
    db.flush()
    nuevas = detectar(db, cierre)  # la detección corre en la misma transacción
    db.commit()

    cierre = db.scalar(select(CierreCaja).options(*_CARGA_CIERRE).where(CierreCaja.id == cierre.id))
    permiso = tiene_accion(db, actual, INHABILITAR_CIERRE)
    return CierreCreado(**_cierre_out(cierre, actual, permiso), alertas_generadas=len(nuevas))


@router.post("/cierres/{cierre_id}/inhabilitar", response_model=CierreOut)
def inhabilitar_cierre(cierre_id: int, datos: InhabilitarIn,
                       actual: UsuarioActual = Depends(requiere_modulo("CIERRES")),
                       _: UsuarioActual = Depends(requiere_accion(INHABILITAR_CIERRE)),
                       db: Session = Depends(get_db)):
    """Marca el cierre como inhabilitado, sin borrarlo, y descarta sus alertas pendientes."""
    cierre = db.get(CierreCaja, cierre_id)
    if cierre is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cierre no encontrado")
    if cierre.registrado_por_id == actual.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Segregación de funciones: no puedes inhabilitar un cierre que registraste")

    motivo = datos.motivo.strip()
    # UPDATE condicional: si dos personas lo intentan a la vez, solo una lo logra
    resultado = db.execute(
        update(CierreCaja).where(CierreCaja.id == cierre_id, CierreCaja.estado == "activo")
        .values(estado="inhabilitado")
    )
    if resultado.rowcount == 0:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "El cierre ya está inhabilitado")

    db.add(CierreHistorial(cierre_id=cierre_id, estado_anterior="activo", estado_nuevo="inhabilitado",
                           usuario_id=actual.id, motivo=motivo))

    # Todo en la misma transacción: o queda el cierre y sus alertas, o no queda nada
    pendientes = db.scalars(select(Alerta).where(Alerta.cierre_id == cierre_id,
                                                 Alerta.estado == "pendiente")).all()
    for alerta in pendientes:
        alerta.estado = "descartada"
        db.add(AlertaHistorial(alerta_id=alerta.id, estado_anterior="pendiente", estado_nuevo="descartada",
                               usuario_id=actual.id, comentario=f"Cierre inhabilitado: {motivo}"))
    db.commit()
    db.expire_all()

    cierre = db.scalar(select(CierreCaja).options(*_CARGA_CIERRE).where(CierreCaja.id == cierre_id))
    return CierreOut(**_cierre_out(cierre, actual, True))


# ================================================================ Alertas
@router.get("/alertas", response_model=list[AlertaOut])
def listar_alertas(
    estado: str | None = Query(None, pattern="^(pendiente|revisada|descartada)$"),
    regla: str | None = Query(None, pattern="^(FUERA_DE_RANGO|TRANSPOSICION|REINCIDENCIA|DUPLICADO)$"),
    severidad: str | None = Query(None, pattern="^(baja|media|alta)$"),
    cajero_id: int | None = None,
    actual: UsuarioActual = Depends(requiere_modulo("ALERTAS")), db: Session = Depends(get_db),
):
    q = select(Alerta).options(*_CARGA_ALERTA).join(CierreCaja)
    if estado:
        q = q.where(Alerta.estado == estado)
    if regla:
        q = q.where(Alerta.regla == regla)
    if severidad:
        q = q.where(Alerta.severidad == severidad)
    if cajero_id:
        q = q.where(CierreCaja.cajero_id == cajero_id)
    # Primero lo más urgente: pendientes, luego severidad alta
    q = q.order_by(case((Alerta.estado == "pendiente", 0), else_=1),
                   case({"alta": 0, "media": 1, "baja": 2}, value=Alerta.severidad),
                   CierreCaja.fecha.desc(), Alerta.id)
    escribe = permisos_de(db, actual).get("ALERTAS") == "escritura"
    return [_alerta_out(a, actual, escribe) for a in db.scalars(q).unique()]


@router.get("/alertas/resumen", response_model=ResumenAlertas)
def resumen_alertas(_: UsuarioActual = Depends(requiere_modulo("ALERTAS")), db: Session = Depends(get_db)):
    def conteo(col, *filtros):
        return [ConteoOut(clave=k, total=n) for k, n in
                db.execute(select(col, func.count()).where(*filtros).group_by(col).order_by(col))]

    riesgo = db.execute(
        select(Cajero.id, Cajero.nombre, Tienda.nombre, func.count(Alerta.id))
        .join(CierreCaja, CierreCaja.cajero_id == Cajero.id)
        .join(Alerta, Alerta.cierre_id == CierreCaja.id)
        .join(Tienda, Tienda.id == Cajero.tienda_id)
        .where(Alerta.estado == "pendiente")
        .group_by(Cajero.id, Cajero.nombre, Tienda.nombre)
        .order_by(func.count(Alerta.id).desc(), Cajero.nombre).limit(5)
    )
    return ResumenAlertas(
        por_estado=conteo(Alerta.estado),
        por_regla=conteo(Alerta.regla),
        por_severidad_pendientes=conteo(Alerta.severidad, Alerta.estado == "pendiente"),
        cajeros_con_mas_alertas=[CajeroRiesgo(cajero_id=i, cajero=n, tienda=t, alertas_abiertas=k)
                                 for i, n, t, k in riesgo],
    )


@router.get("/alertas/parametros", response_model=list[ParametroOut])
def parametros(_: UsuarioActual = Depends(requiere_modulo("ALERTAS")), db: Session = Depends(get_db)):
    return [ParametroOut(clave=p.clave, valor=p.valor, descripcion=p.descripcion)
            for p in db.scalars(select(ParametroDeteccion).order_by(ParametroDeteccion.clave))]


@router.get("/alertas/{alerta_id}", response_model=AlertaDetalle)
def detalle_alerta(alerta_id: int, actual: UsuarioActual = Depends(requiere_modulo("ALERTAS")),
                   db: Session = Depends(get_db)):
    alerta = db.scalar(select(Alerta).options(*_CARGA_ALERTA).where(Alerta.id == alerta_id))
    if alerta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alerta no encontrada")
    escribe = permisos_de(db, actual).get("ALERTAS") == "escritura"
    return _alerta_out(alerta, actual, escribe, con_historial=True)


@router.post("/alertas/{alerta_id}/gestion", response_model=AlertaDetalle)
def gestionar_alerta(alerta_id: int, datos: GestionIn,
                     actual: UsuarioActual = Depends(requiere_modulo("ALERTAS", "escritura")),
                     db: Session = Depends(get_db)):
    alerta = db.scalar(select(Alerta).options(joinedload(Alerta.cierre)).where(Alerta.id == alerta_id))
    if alerta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alerta no encontrada")
    if _registro_el_cierre(alerta, actual):
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Segregación de funciones: no puedes gestionar alertas de un cierre que registraste")

    # UPDATE condicional: solo cambia si SIGUE pendiente. Si dos personas
    # gestionan la misma alerta a la vez, solo una gana; la otra recibe 409.
    resultado = db.execute(
        update(Alerta).where(Alerta.id == alerta_id, Alerta.estado == "pendiente")
        .values(estado=datos.estado)
    )
    if resultado.rowcount == 0:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "La alerta ya fue gestionada")

    db.add(AlertaHistorial(alerta_id=alerta_id, estado_anterior="pendiente", estado_nuevo=datos.estado,
                           usuario_id=actual.id, comentario=datos.comentario.strip()))
    db.commit()
    db.expire_all()
    return detalle_alerta(alerta_id, actual, db)


@router.post("/alertas/reprocesar")
def reprocesar(actual: UsuarioActual = Depends(requiere_modulo("ALERTAS", "escritura")),
               db: Session = Depends(get_db)):
    """Vuelve a correr la detección sobre todos los cierres (solo Admin). Es idempotente."""
    if not actual.es_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el Administrador puede reprocesar")
    nuevas = reprocesar_todo(db)
    db.commit()
    return {"alertas_nuevas": nuevas}
