"""Pruebas del proceso completo: registrar cierre -> alerta -> gestión -> historial."""
from datetime import date, timedelta

from io import BytesIO

import pytest
from pypdf import PdfReader
from sqlalchemy import delete

from app.database import SessionLocal
from app.deteccion import _anomalias_en_ventana
from app.models import CierreCaja, PermisoAccion


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


# ------------------------------------------------------------ inhabilitar
MOTIVO = "Error de carga confirmado con la tienda"


def _cierre_con_alerta_pendiente(login):
    alerta = login("jefe_contraloria").get("/api/alertas?estado=pendiente").json()[0]
    return alerta["cierre_id"], alerta["id"]


@pytest.mark.parametrize("quien", ["jefe_tesoreria", "jefe_contabilidad", "jefe_planificacion"])
def test_solo_los_autorizados_inhabilitan(login, quien):
    cierre_id, _ = _cierre_con_alerta_pendiente(login)
    r = login(quien).post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": MOTIVO})
    assert r.status_code == 403


def test_colaborador_no_puede_inhabilitar(login):
    cierre_id, _ = _cierre_con_alerta_pendiente(login)
    r = login("colab_contraloria").post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": MOTIVO})
    assert r.status_code == 403


def test_contraloria_inhabilita_y_descarta_las_alertas_pendientes(login):
    contraloria = login("jefe_contraloria")
    cierre_id, alerta_id = _cierre_con_alerta_pendiente(login)

    r = contraloria.post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": MOTIVO})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "inhabilitado"
    assert cuerpo["motivo_inhabilitacion"] == MOTIVO
    assert cuerpo["inhabilitado_por"] == "Tomás Iriarte"
    assert cuerpo["puede_inhabilitar"] is False

    alerta = contraloria.get(f"/api/alertas/{alerta_id}").json()
    assert alerta["estado"] == "descartada"
    assert alerta["historial"][-1]["comentario"] == f"Cierre inhabilitado: {MOTIVO}"
    assert alerta["historial"][-1]["usuario"] == "Tomás Iriarte"


def test_el_cierre_inhabilitado_sigue_consultable(login):
    contraloria = login("jefe_contraloria")
    total = len(contraloria.get("/api/cierres").json())
    cierre_id, _ = _cierre_con_alerta_pendiente(login)
    contraloria.post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": MOTIVO})
    assert len(contraloria.get("/api/cierres").json()) == total


def test_inhabilitar_dos_veces_da_conflicto(login):
    contraloria = login("jefe_contraloria")
    cierre_id, _ = _cierre_con_alerta_pendiente(login)
    assert contraloria.post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": MOTIVO}).status_code == 200
    assert contraloria.post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": MOTIVO}).status_code == 409


def test_inhabilitar_exige_motivo(login):
    cierre_id, _ = _cierre_con_alerta_pendiente(login)
    r = login("jefe_contraloria").post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": "corto"})
    assert r.status_code == 422
    assert "Motivo" in r.json()["detail"]


def test_quien_registra_no_inhabilita_ni_siendo_admin(login):
    admin = login("admin")
    creado = admin.post("/api/cierres", json=_cierre("1000.00", "2000.00")).json()
    assert creado["puede_inhabilitar"] is False
    r = admin.post(f"/api/cierres/{creado['id']}/inhabilitar", json={"motivo": MOTIVO})
    assert r.status_code == 403
    # Otra persona autorizada sí puede
    r = login("jefe_contraloria").post(f"/api/cierres/{creado['id']}/inhabilitar", json={"motivo": MOTIVO})
    assert r.status_code == 200


def test_el_permiso_se_define_en_la_base_de_datos(login):
    """Si se quita la fila de permiso_accion, Contraloría pierde el permiso sin tocar código."""
    cierre_id, _ = _cierre_con_alerta_pendiente(login)
    contraloria = login("jefe_contraloria")
    assert contraloria.get("/api/cierres").json()[0]["puede_inhabilitar"] is True

    with SessionLocal() as db:
        db.execute(delete(PermisoAccion).where(PermisoAccion.departamento_id.is_not(None)))
        db.commit()

    assert contraloria.get("/api/cierres").json()[0]["puede_inhabilitar"] is False
    r = contraloria.post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": MOTIVO})
    assert r.status_code == 403


def test_el_cierre_inhabilitado_no_cuenta_para_reincidencia(login):
    tesoreria = login("jefe_tesoreria")
    primero = tesoreria.post("/api/cierres", json=_cierre("1000.00", "2000.00")).json()
    ultimo = tesoreria.post("/api/cierres", json=_cierre("3000.00", "5000.00", fecha=date.today() - timedelta(days=1))).json()

    # La ventana mira hacia atrás, así que se revisa desde el cierre más reciente
    with SessionLocal() as db:
        referencia = db.get(CierreCaja, primero["id"])
        assert ultimo["id"] in {c.id for c in _anomalias_en_ventana(db, referencia, 30)}

    login("jefe_contraloria").post(f"/api/cierres/{ultimo['id']}/inhabilitar", json={"motivo": MOTIVO})

    with SessionLocal() as db:
        referencia = db.get(CierreCaja, primero["id"])
        assert ultimo["id"] not in {c.id for c in _anomalias_en_ventana(db, referencia, 30)}


# ------------------------------------------------------------ reporte PDF
def _texto_pdf(respuesta) -> str:
    return " ".join(p.extract_text() for p in PdfReader(BytesIO(respuesta.content)).pages)


def test_reporte_pdf_se_descarga_con_los_cierres(login):
    r = login("jefe_tesoreria").get("/api/cierres/reporte.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "attachment" in r.headers["content-disposition"]
    texto = _texto_pdf(r)
    assert "Reporte de cierres de caja" in texto
    assert "Lucía Paredes" in texto
    assert "Cierres: 60" in texto
    assert "6.765,86" in texto  # formato venezolano, sin perder decimales


def test_reporte_pdf_respeta_los_filtros(login):
    cliente = login("jefe_tesoreria")
    filtrados = cliente.get("/api/cierres?tienda_id=1").json()
    texto = _texto_pdf(cliente.get("/api/cierres/reporte.pdf?tienda_id=1"))
    assert f"Cierres: {len(filtrados)}" in texto
    assert filtrados[0]["tienda"] in texto
    assert "Filtros: tienda" in texto


@pytest.mark.parametrize("quien", ["colab_tesoreria", "jefe_contabilidad"])
def test_reporte_pdf_exige_el_modulo(login, quien):
    assert login(quien).get("/api/cierres/reporte.pdf").status_code == 403


def test_reporte_pdf_exige_sesion(cliente):
    assert cliente.get("/api/cierres/reporte.pdf").status_code == 401


def test_reporte_pdf_muestra_el_cierre_inhabilitado_y_escapa_el_motivo(login):
    """Un motivo con etiquetas no debe romper el PDF: se escribe como texto."""
    contraloria = login("jefe_contraloria")
    cierre_id, _ = _cierre_con_alerta_pendiente(login)
    motivo = "Error <b>de</b> carga & revisado"
    assert contraloria.post(f"/api/cierres/{cierre_id}/inhabilitar", json={"motivo": motivo}).status_code == 200

    r = contraloria.get("/api/cierres/reporte.pdf")
    assert r.status_code == 200
    texto = _texto_pdf(r)
    assert "Inhabilitados: 1" in texto
    assert "Error <b>de</b> carga & revisado" in texto.replace("\n", " ")


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
