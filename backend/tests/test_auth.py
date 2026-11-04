"""Pruebas de autenticación."""
from tests.conftest import CUENTAS, PASSWORD


def test_login_correcto_pone_cookie_httponly(cliente):
    r = cliente.post("/api/auth/login", json={"correo": CUENTAS["jefe_tesoreria"], "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["rol"] == "JEFE_DEPTO"
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert "password" not in r.text.lower()


def test_correo_inexistente_y_clave_mala_dan_el_mismo_mensaje(cliente):
    a = cliente.post("/api/auth/login", json={"correo": "nadie@vpfinanzas.example", "password": "x"})
    b = cliente.post("/api/auth/login", json={"correo": CUENTAS["jefe_contabilidad"], "password": "mala"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()  # no revela si el correo existe


def test_colaborador_inactivo_no_puede_entrar(cliente):
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import Colaborador
    with SessionLocal() as db:
        correo = db.scalar(select(Colaborador.correo).where(Colaborador.estado == "inactivo"))
    r = cliente.post("/api/auth/login", json={"correo": correo, "password": PASSWORD})
    assert r.status_code == 401


def test_bloqueo_tras_5_intentos_fallidos(cliente, bd_limpia):
    correo = CUENTAS["jefe_planificacion"]
    for _ in range(5):
        assert cliente.post("/api/auth/login", json={"correo": correo, "password": "mala"}).status_code == 401
    # Bloqueada: ni siquiera la contraseña correcta funciona durante 15 minutos
    r = cliente.post("/api/auth/login", json={"correo": correo, "password": PASSWORD})
    assert r.status_code == 429


def test_sin_sesion_no_hay_datos(cliente):
    assert cliente.get("/api/perfil").status_code == 401
    assert cliente.get("/api/departamentos").status_code == 401


def test_token_alterado_es_rechazado(cliente):
    cliente.cookies.set("portal_sesion", "eyJhbGciOiJub25lIn0.eyJzdWIiOiIxIn0.")  # alg=none
    assert cliente.get("/api/auth/me").status_code == 401


def test_logout_borra_la_sesion(login):
    c = login("colab_tesoreria")
    assert c.get("/api/auth/me").status_code == 200
    c.post("/api/auth/logout")
    assert c.get("/api/auth/me").status_code == 401
