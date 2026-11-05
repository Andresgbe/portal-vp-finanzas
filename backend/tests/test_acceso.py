"""Pruebas de control de acceso por rol y departamento.

Cada prueba llama directo a la API (sin frontend): demuestra que la
seguridad está en el backend y no depende de ocultar botones.
"""
import pytest


@pytest.fixture
def ids_departamentos(login):
    admin = login("admin")
    return {d["nombre"]: d["id"] for d in admin.get("/api/departamentos").json()}


# ------------------------------------------------------------ módulos por rol
@pytest.mark.parametrize("quien, esperados", [
    ("admin", {"MI_PERFIL": "escritura", "DEPARTAMENTOS": "escritura", "DIRECTORIO": "escritura", "ESTRUCTURA": "escritura",
               "CIERRES": "escritura", "ALERTAS": "escritura"}),
    ("jefe_tesoreria", {"MI_PERFIL": "lectura", "DEPARTAMENTOS": "lectura", "DIRECTORIO": "lectura", "ESTRUCTURA": "lectura",
                        "CIERRES": "escritura", "ALERTAS": "lectura"}),
    ("jefe_contraloria", {"MI_PERFIL": "lectura", "DEPARTAMENTOS": "lectura", "DIRECTORIO": "lectura", "ESTRUCTURA": "lectura",
                          "CIERRES": "lectura", "ALERTAS": "escritura"}),
    ("jefe_contabilidad", {"MI_PERFIL": "lectura", "DEPARTAMENTOS": "lectura", "DIRECTORIO": "lectura", "ESTRUCTURA": "lectura"}),
    ("colab_tesoreria", {"MI_PERFIL": "lectura", "DEPARTAMENTOS": "lectura", "DIRECTORIO": "lectura"}),
])
def test_modulos_visibles_segun_rol_y_departamento(login, quien, esperados):
    modulos = login(quien).get("/api/auth/me").json()["modulos"]
    assert {m["codigo"]: m["nivel_acceso"] for m in modulos} == esperados


# ------------------------------------------------------------ alcance de departamento
def test_admin_ve_todos_los_departamentos(login):
    assert len(login("admin").get("/api/departamentos").json()) == 4


def test_jefe_solo_ve_su_departamento(login):
    deptos = login("jefe_contabilidad").get("/api/departamentos").json()
    assert [d["nombre"] for d in deptos] == ["Contabilidad"]


def test_jefe_no_puede_pedir_colaboradores_de_otro_departamento(login, ids_departamentos):
    jefe = login("jefe_contabilidad")
    r = jefe.get(f"/api/departamentos/{ids_departamentos['Tesorería']}/colaboradores")
    assert r.status_code == 403
    r = jefe.get(f"/api/departamentos/{ids_departamentos['Tesorería']}/estructura")
    assert r.status_code == 403


def test_jefe_ve_detalle_completo_de_su_departamento(login, ids_departamentos):
    filas = login("jefe_tesoreria").get(
        f"/api/departamentos/{ids_departamentos['Tesorería']}/colaboradores").json()
    assert len(filas) == 10
    assert {"fecha_ingreso", "pais", "estado"} <= filas[0].keys()


def test_colaborador_ve_informacion_limitada(login, ids_departamentos):
    filas = login("colab_tesoreria").get(
        f"/api/departamentos/{ids_departamentos['Tesorería']}/colaboradores").json()
    assert len(filas) == 9  # sin el colaborador inactivo
    assert set(filas[0].keys()) == {"id", "nombre", "cargo", "correo"}


def test_colaborador_solo_ve_su_propia_ficha(login):
    c = login("colab_tesoreria")
    yo = c.get("/api/auth/me").json()["colaborador_id"]
    assert c.get(f"/api/colaboradores/{yo}").status_code == 200
    jefa = login("jefe_tesoreria").get("/api/auth/me").json()["colaborador_id"]
    assert c.get(f"/api/colaboradores/{jefa}").status_code == 403


def test_colaborador_no_accede_a_modulo_estructura(login, ids_departamentos):
    r = login("colab_tesoreria").get(f"/api/departamentos/{ids_departamentos['Tesorería']}/estructura")
    assert r.status_code == 403


def test_jefe_no_ve_ficha_de_otro_departamento(login):
    otro = login("colab_contraloria").get("/api/auth/me").json()["colaborador_id"]
    assert login("jefe_tesoreria").get(f"/api/colaboradores/{otro}").status_code == 403
    assert login("admin").get(f"/api/colaboradores/{otro}").status_code == 200


def test_perfil_incluye_funciones_del_cargo(login):
    perfil = login("jefe_contraloria").get("/api/perfil").json()
    assert perfil["cargo"] == "Gerente de Contraloría"
    assert "Resolver alertas de anomalías de caja" in perfil["funciones"]


def test_departamentos_admin_ve_los_cuatro_y_los_demas_solo_el_propio(login):
    nombres = lambda quien: [d["nombre"] for d in login(quien).get("/api/departamentos").json()]
    assert len(nombres("admin")) == 4
    assert nombres("jefe_contraloria") == ["Contraloría"]
    assert nombres("colab_tesoreria") == ["Tesorería"]
