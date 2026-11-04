"""Pruebas del motor de detección (reglas de negocio)."""
from collections import Counter
from decimal import Decimal as D

import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.deteccion import evaluar_montos, posicion_transposicion
from app.models import Alerta

PARAMS = {
    "TOLERANCIA_ABSOLUTA": D("10"), "SEVERIDAD_MEDIA_PCT": D("2"), "SEVERIDAD_ALTA_PCT": D("10"),
    "SEVERIDAD_ALTA_MONTO": D("500"), "VENTANA_REINCIDENCIA_DIAS": D("30"),
    "MIN_ANOMALIAS_REINCIDENCIA": D("3"),
}


# ------------------------------------------------------------ transposición
@pytest.mark.parametrize("a, b", [
    ("4518.95", "4158.95"),  # cierre #53
    ("9485.87", "4985.87"),  # cierre #57: el primer dígito
    ("3954.90", "3945.90"),  # cierre #58: diferencia de solo 9,00
    ("573.95", "753.95"),    # cierre #19
    ("1250.00", "1520.00"),  # ejemplo del enunciado
    ("100.21", "100.12"),    # en los céntimos
])
def test_detecta_transposicion(a, b):
    assert posicion_transposicion(D(a), D(b)) is not None


@pytest.mark.parametrize("a, b, por_que", [
    ("6947.75", "6767.75", "difiere 180 (múltiplo de 9) pero NO es transposición"),
    ("1700.16", "1880.16", "difiere 180 (múltiplo de 9) pero NO es transposición"),
    ("1147.97", "967.97", "distinta cantidad de dígitos"),
    ("1250.00", "1250.00", "montos iguales"),
    ("1250.00", "0251.00", "no son vecinos"),
    ("1234.00", "4231.00", "dígitos intercambiados no vecinos"),
])
def test_no_confunde_multiplo_de_9_con_transposicion(a, b, por_que):
    assert posicion_transposicion(D(a), D(b)) is None, por_que


# ------------------------------------------------------------ rango y severidad
def test_ruido_dentro_de_tolerancia_no_genera_alerta():
    assert evaluar_montos(D("5361.46"), D("5360.97"), PARAMS) is None  # 0,49
    assert evaluar_montos(D("4390.24"), D("4395.05"), PARAMS) is None  # 4,81 (el mayor ruido)


def test_transposicion_se_detecta_aunque_este_dentro_de_tolerancia():
    h = evaluar_montos(D("3954.90"), D("3945.90"), PARAMS)
    assert h.regla == "TRANSPOSICION"


def test_fuera_de_rango_y_severidad():
    assert evaluar_montos(D("6947.75"), D("6767.75"), PARAMS).severidad == "media"  # sobrante 2,66 %
    assert evaluar_montos(D("1253.16"), D("2017.42"), PARAMS).severidad == "alta"   # faltante 37,88 %


def test_un_faltante_es_mas_grave_que_un_sobrante_igual():
    sobrante = evaluar_montos(D("1030.00"), D("1000.00"), PARAMS)
    faltante = evaluar_montos(D("970.00"), D("1000.00"), PARAMS)
    assert (sobrante.severidad, faltante.severidad) == ("media", "alta")


# ------------------------------------------------------------ dataset completo
def test_resultado_sobre_el_dataset_oficial(bd_limpia):
    with SessionLocal() as db:
        alertas = db.scalars(select(Alerta)).all()
        por_regla = Counter(a.regla for a in alertas)
        reincidentes = sorted(a.cierre.cajero.nombre for a in alertas if a.regla == "REINCIDENCIA")
    assert por_regla == {"FUERA_DE_RANGO": 14, "TRANSPOSICION": 5, "DUPLICADO": 6, "REINCIDENCIA": 3}
    assert reincidentes == ["Hugo Sandoval", "Wilmer Colmenares", "Yelitza Bravo"]


def test_todas_las_alertas_nacen_pendientes_con_historial(bd_limpia):
    with SessionLocal() as db:
        for a in db.scalars(select(Alerta)):
            assert a.estado == "pendiente"
            assert a.historial[0].estado_nuevo == "pendiente" and a.historial[0].usuario_id is None


def test_reprocesar_es_idempotente(login):
    r = login("admin").post("/api/alertas/reprocesar")
    assert r.json() == {"alertas_nuevas": 0}
