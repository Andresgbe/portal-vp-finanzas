"""Pruebas del proceso completo: registrar cierre -> alerta -> gestión -> historial."""
from datetime import date, timedelta

import pytest


def _cierre(declarado: str, sistema: str, cajero_id=5, tienda_id=1, fecha=None):
    return {"tienda_id": tienda_id, "cajero_id": cajero_id,
            "fecha": (fecha or date.today()).isoformat(),
            "monto_declarado": declarado, "monto_sistema": sistema}


@pytest.fixture(autouse=True)
def _limpia(bd_limpia):
    """Cada prueba de este archivo parte de la BD recién sembrada."""
    yield


# ------------------------------------------------------------ registro
def test_tesoreria_registra_cierre_y_se_detecta_transposicion(login):
    r = login("jefe_tesoreria").post("/api/cierres", json=_cierre("1520.00", "1250.00"))
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["alertas_generadas"] == 1
    assert cuerpo["alertas"][0]["regla"] == "TRANSPOSICION"
    assert cuerpo["registrado_por"] == "Lucía Paredes"


def test_cierre_sin_diferencia_no_genera_alertas(login):
    r = login("jefe_tesoreria").post("/api/cierres", json=_cierre("800.50", "800.50"))
    assert r.status_code == 201 and r.json()["alertas_generadas"] == 0


@pytest.mark.parametrize("quien", ["jefe_contraloria", "jefe_contabilidad", "colab_tesoreria"])
def test_solo_tesoreria_y_admin_registran_cierres(login, quien):
    r = login(quien).post("/api/cierres", json=_cierre("100.00", "100.00"))
    assert r.status_code == 403


@pytest.mark.parametrize("datos, mensaje", [
    (_cierre("100.00", "100.00", cajero_id=5, tienda_id=2), "no pertenece"),
    (_cierre("100.00", "100.00", fecha=date.today() + timedelta(days=1)), "futura"),
    (_cierre("100.00", "100.00", cajero_id=999), "no existe"),
])
def test_validaciones_de_negocio(login, datos, mensaje):
    r = login("jefe_tesoreria").post("/api/cierres", json=datos)
    assert r.status_code == 422 and mensaje in r.text


@pytest.mark.parametrize("campo, valor", [("monto_declarado", "-5"), ("monto_sistema", "10.999")])
def test_montos_invalidos_se_rechazan(login, campo, valor):
    datos = _cierre("100.00", "100.00")
    datos[campo] = valor
    assert login("jefe_tesoreria").post("/api/cierres", json=datos).status_code == 422


def test_segundo_cierre_mismo_dia_genera_duplicado(login):
    c = login("jefe_tesoreria")
    c.post("/api/cierres", json=_cierre("500.00", "500.00"))
    r = c.post("/api/cierres", json=_cierre("700.00", "700.00"))
    assert [a["regla"] for a in r.json()["alertas"]] == ["DUPLICADO"]


def test_tercera_anomalia_en_30_dias_dispara_reincidencia(login):
    c = login("jefe_tesoreria")
    hoy = date.today()
    for i, monto in enumerate(["900.00", "850.00"]):
        c.post("/api/cierres", json=_cierre(monto, "1000.00", fecha=hoy - timedelta(days=10 - i)))
    r = c.post("/api/cierres", json=_cierre("800.00", "1000.00", fecha=hoy))
    assert {a["regla"] for a in r.json()["alertas"]} == {"FUERA_DE_RANGO", "REINCIDENCIA"}


# ------------------------------------------------------------ gestión de alertas
def _primera_pendiente(cliente) -> dict:
    return cliente.get("/api/alertas", params={"estado": "pendiente"}).json()[0]


def test_contraloria_gestiona_alerta_y_queda_en_historial(login):
    c = login("jefe_contraloria")
    alerta = _primera_pendiente(c)
    r = c.post(f"/api/alertas/{alerta['id']}/gestion",
               json={"estado": "revisada", "comentario": "Confirmado con la tienda, se abre caso."})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["estado"] == "revisada"
    assert d["gestionada_por"] == "Tomás Iriarte"
    assert [h["estado_nuevo"] for h in d["historial"]] == ["pendiente", "revisada"]
    assert d["historial"][-1]["usuario"] == "Tomás Iriarte"


def test_no_se_gestiona_dos_veces(login):
    c = login("jefe_contraloria")
    alerta = _primera_pendiente(c)
    datos = {"estado": "descartada", "comentario": "Falso positivo, conteo verificado."}
    assert c.post(f"/api/alertas/{alerta['id']}/gestion", json=datos).status_code == 200
    assert c.post(f"/api/alertas/{alerta['id']}/gestion", json=datos).status_code == 409


def test_comentario_obligatorio(login):
    c = login("jefe_contraloria")
    alerta = _primera_pendiente(c)
    r = c.post(f"/api/alertas/{alerta['id']}/gestion", json={"estado": "revisada", "comentario": "ok"})
    assert r.status_code == 422


def test_tesoreria_ve_alertas_pero_no_puede_gestionarlas(login):
    c = login("jefe_tesoreria")
    alerta = _primera_pendiente(c)
    assert alerta["puede_gestionar"] is False
    r = c.post(f"/api/alertas/{alerta['id']}/gestion",
               json={"estado": "revisada", "comentario": "Intento desde Tesorería"})
    assert r.status_code == 403


def test_colaborador_no_ve_alertas(login):
    assert login("colab_contraloria").get("/api/alertas").status_code == 403


def test_segregacion_quien_registra_no_gestiona_ni_siendo_admin(login):
    admin = login("admin")
    creado = admin.post("/api/cierres", json=_cierre("1000.00", "2000.00")).json()
    alerta_id = creado["alertas"][0]["id"]

    detalle = admin.get(f"/api/alertas/{alerta_id}").json()
    assert detalle["puede_gestionar"] is False
    r = admin.post(f"/api/alertas/{alerta_id}/gestion",
                   json={"estado": "descartada", "comentario": "Me autoapruebo esta alerta"})
    assert r.status_code == 403
    # Otra persona (Contraloría) sí puede
    r = login("jefe_contraloria").post(f"/api/alertas/{alerta_id}/gestion",
                                       json={"estado": "revisada", "comentario": "Revisado por Contraloría"})
    assert r.status_code == 200


def test_descartar_alertas_evita_reincidencia_futura(login):
    """Una alerta descartada (falso positivo) no cuenta para reincidencia."""
    tes, con = login("jefe_tesoreria"), login("jefe_contraloria")
    hoy = date.today()
    for i, monto in enumerate(["900.00", "850.00"]):
        creado = tes.post("/api/cierres", json=_cierre(monto, "1000.00", fecha=hoy - timedelta(days=10 - i))).json()
        con.post(f"/api/alertas/{creado['alertas'][0]['id']}/gestion",
                 json={"estado": "descartada", "comentario": "Error del sistema POS, no del cajero"})
    r = tes.post("/api/cierres", json=_cierre("800.00", "1000.00", fecha=hoy))
    assert [a["regla"] for a in r.json()["alertas"]] == ["FUERA_DE_RANGO"]


def test_resumen_de_alertas(login):
    r = login("jefe_contraloria").get("/api/alertas/resumen").json()
    assert sum(x["total"] for x in r["por_estado"]) == 28
    assert r["cajeros_con_mas_alertas"][0]["alertas_abiertas"] >= 3
