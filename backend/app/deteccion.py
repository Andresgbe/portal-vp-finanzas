"""Motor de detección de anomalías en cierres de caja.

Reglas (los umbrales viven en la tabla parametro_deteccion):

  TRANSPOSICION   Los dos montos son iguales salvo dos dígitos vecinos
                  intercambiados (ej. 4518,95 vs 4158,95). Se evalúa ANTES que
                  el rango y sin importar la tolerancia: 3954,90 vs 3945,90
                  difiere solo 9,00 y pasaría desapercibido por la regla de rango.
  FUERA_DE_RANGO  |declarado - sistema| > tolerancia. Severidad según % y monto;
                  un faltante (declarado < sistema) sube un nivel.
  DUPLICADO       Un segundo cierre del mismo cajero en la misma fecha.
  REINCIDENCIA    El cajero acumula N cierres anómalos en una ventana de días.

Dato clave: si dos montos difieren por una transposición de dígitos, su
diferencia SIEMPRE es múltiplo de 9. Pero lo contrario no es cierto
(6947,75 vs 6767,75 difieren 180 = 9 x 20 y no es transposición), por eso
el sistema compara los dígitos uno a uno y usa el múltiplo de 9 solo como
dato de apoyo.
"""
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Alerta, AlertaHistorial, CierreCaja, ParametroDeteccion

ORDEN_SEVERIDAD = ["baja", "media", "alta"]
REGLAS_DE_MONTO = ("FUERA_DE_RANGO", "TRANSPOSICION")  # cuentan para reincidencia


@dataclass
class Hallazgo:
    regla: str
    severidad: str
    detalle: str


def _fmt(m: Decimal) -> str:
    """1234.5 -> '1.234,50' (formato venezolano)."""
    return f"{m:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _centimos(m: Decimal) -> str:
    """4518.95 -> '451895' (dígitos sin separador decimal)."""
    return str(int((m * 100).to_integral_value()))


def posicion_transposicion(a: Decimal, b: Decimal) -> int | None:
    """Si b es a con dos dígitos VECINOS intercambiados, devuelve la posición
    del primero de esos dígitos (0 = el de más a la izquierda). Si no, None."""
    x, y = _centimos(a), _centimos(b)
    if x == y or len(x) != len(y):
        return None
    distintos = [i for i in range(len(x)) if x[i] != y[i]]
    if len(distintos) != 2:
        return None
    i, j = distintos
    if j == i + 1 and x[i] == y[j] and x[j] == y[i]:
        return i
    return None


def _subir(severidad: str) -> str:
    return ORDEN_SEVERIDAD[min(ORDEN_SEVERIDAD.index(severidad) + 1, 2)]


def cargar_parametros(db: Session) -> dict[str, Decimal]:
    return {p.clave: p.valor for p in db.scalars(select(ParametroDeteccion))}


def evaluar_montos(declarado: Decimal, sistema: Decimal, p: dict[str, Decimal]) -> Hallazgo | None:
    """Reglas que solo miran los dos montos de UN cierre (función pura, sin BD)."""
    dif = declarado - sistema
    abs_dif = abs(dif)
    tipo = "faltante" if dif < 0 else "sobrante"

    pos = posicion_transposicion(declarado, sistema)
    if pos is not None:
        sev = "alta" if abs_dif >= p["SEVERIDAD_ALTA_MONTO"] else "media"
        digitos = _centimos(declarado)[pos:pos + 2]
        return Hallazgo(
            "TRANSPOSICION", sev,
            f"Probable error de digitación: declarado {_fmt(declarado)} vs sistema {_fmt(sistema)} "
            f"(dígitos '{digitos}' intercambiados). {tipo.capitalize()} de {_fmt(abs_dif)}; "
            f"la diferencia es múltiplo de 9 ({_fmt(abs_dif)} = 9 × {_fmt(abs_dif / 9)}).",
        )

    if abs_dif > p["TOLERANCIA_ABSOLUTA"]:
        pct = (abs_dif / sistema * 100) if sistema else Decimal("100")
        if pct >= p["SEVERIDAD_ALTA_PCT"] or abs_dif >= p["SEVERIDAD_ALTA_MONTO"]:
            sev = "alta"
        elif pct >= p["SEVERIDAD_MEDIA_PCT"]:
            sev = "media"
        else:
            sev = "baja"
        if tipo == "faltante":
            sev = _subir(sev)  # falta dinero en caja: es más grave que un sobrante
        return Hallazgo(
            "FUERA_DE_RANGO", sev,
            f"{tipo.capitalize()} de {_fmt(abs_dif)} ({_fmt(pct)} % del monto sistema); "
            f"tolerancia {_fmt(p['TOLERANCIA_ABSOLUTA'])}.",
        )
    return None


# ---------------------------------------------------------------------
# Reglas que necesitan mirar otros cierres (usan la BD)
# ---------------------------------------------------------------------
def _buscar_duplicado(db: Session, cierre: CierreCaja) -> CierreCaja | None:
    return db.scalar(
        select(CierreCaja)
        .where(CierreCaja.cajero_id == cierre.cajero_id, CierreCaja.fecha == cierre.fecha,
               CierreCaja.id < cierre.id)
        .order_by(CierreCaja.id)
    )


def _anomalias_en_ventana(db: Session, cierre: CierreCaja, dias: int) -> list[CierreCaja]:
    """Cierres del mismo cajero, en la ventana, con alerta de monto no descartada."""
    desde = cierre.fecha - timedelta(days=dias)
    return list(db.scalars(
        select(CierreCaja).distinct()
        .join(Alerta, Alerta.cierre_id == CierreCaja.id)
        .where(CierreCaja.cajero_id == cierre.cajero_id,
               CierreCaja.fecha.between(desde, cierre.fecha),
               Alerta.regla.in_(REGLAS_DE_MONTO),
               Alerta.estado != "descartada")
        .order_by(CierreCaja.fecha, CierreCaja.id)
    ))


def _ya_hay_reincidencia_en_ventana(db: Session, cierre: CierreCaja, dias: int) -> bool:
    desde = cierre.fecha - timedelta(days=dias)
    return db.scalar(
        select(Alerta.id).join(CierreCaja, CierreCaja.id == Alerta.cierre_id)
        .where(CierreCaja.cajero_id == cierre.cajero_id, Alerta.regla == "REINCIDENCIA",
               CierreCaja.fecha.between(desde, cierre.fecha))
        .limit(1)
    ) is not None


def _crear_alerta(db: Session, cierre: CierreCaja, h: Hallazgo) -> Alerta | None:
    existe = db.scalar(select(Alerta.id).where(Alerta.cierre_id == cierre.id, Alerta.regla == h.regla))
    if existe:
        return None  # idempotente: re-ejecutar la detección no duplica alertas
    alerta = Alerta(cierre_id=cierre.id, regla=h.regla, severidad=h.severidad,
                    detalle=h.detalle, estado="pendiente")
    db.add(alerta)
    db.flush()
    db.add(AlertaHistorial(alerta_id=alerta.id, estado_anterior=None, estado_nuevo="pendiente",
                           usuario_id=None, comentario=f"Creada por detección automática ({h.regla})"))
    return alerta


def detectar(db: Session, cierre: CierreCaja, p: dict[str, Decimal] | None = None) -> list[Alerta]:
    """Aplica todas las reglas a un cierre ya guardado. Devuelve las alertas nuevas."""
    p = p or cargar_parametros(db)
    nuevas: list[Alerta] = []

    hallazgo = evaluar_montos(cierre.monto_declarado, cierre.monto_sistema, p)
    if hallazgo and (a := _crear_alerta(db, cierre, hallazgo)):
        nuevas.append(a)

    if (previo := _buscar_duplicado(db, cierre)) is not None:
        h = Hallazgo("DUPLICADO", "media",
                     f"El cajero ya tiene el cierre #{previo.id} en la misma fecha "
                     f"({cierre.fecha:%d/%m/%Y}). Debería existir un único cierre por cajero y día.")
        if a := _crear_alerta(db, cierre, h):
            nuevas.append(a)

    if hallazgo:
        dias = int(p["VENTANA_REINCIDENCIA_DIAS"])
        minimo = int(p["MIN_ANOMALIAS_REINCIDENCIA"])
        previos = _anomalias_en_ventana(db, cierre, dias)
        if len(previos) >= minimo and not _ya_hay_reincidencia_en_ventana(db, cierre, dias):
            ids = ", ".join(f"#{c.id} ({c.fecha:%d/%m})" for c in previos)
            h = Hallazgo("REINCIDENCIA", "alta",
                         f"{cierre.cajero.nombre} acumula {len(previos)} cierres con anomalía "
                         f"en {dias} días: {ids}.")
            if a := _crear_alerta(db, cierre, h):
                nuevas.append(a)
    return nuevas


def reprocesar_todo(db: Session) -> int:
    """Corre la detección sobre todos los cierres en orden cronológico."""
    p = cargar_parametros(db)
    total = 0
    for cierre in db.scalars(select(CierreCaja).order_by(CierreCaja.fecha, CierreCaja.id)).all():
        total += len(detectar(db, cierre, p))
    return total
