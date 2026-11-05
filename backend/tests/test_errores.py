"""Pruebas del formato de los errores que recibe el frontend."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import montar_frontend


def test_validacion_devuelve_un_texto_en_espanol(login):
    r = login("jefe_contraloria").post("/api/alertas/1/gestion",
                                       json={"estado": "revisada", "comentario": "corto"})
    assert r.status_code == 422
    assert r.json()["detail"] == 'El campo "Comentario" debe tener al menos 10 caracteres.'


def test_validacion_reune_todos_los_campos_con_error(cliente):
    r = cliente.post("/api/auth/login", json={})
    assert r.status_code == 422
    detalle = r.json()["detail"]
    assert 'El campo "Correo" es obligatorio.' in detalle
    assert 'El campo "Contraseña" es obligatorio.' in detalle


def test_validacion_no_devuelve_lo_que_se_envio(cliente):
    clave = "clave-secreta-" + "x" * 200  # supera el máximo de 128 caracteres
    r = cliente.post("/api/auth/login", json={"correo": "alguien@vpfinanzas.example", "password": clave})
    assert r.status_code == 422
    assert clave not in r.text


def _cliente_con_frontend(tmp_path) -> TestClient:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>SPA</html>")
    aplicacion = FastAPI()
    montar_frontend(aplicacion, tmp_path)
    return TestClient(aplicacion)


def test_ruta_api_inexistente_responde_404_en_json(tmp_path):
    r = _cliente_con_frontend(tmp_path).get("/api/no-existe")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")


def test_rutas_del_frontend_siguen_sirviendo_la_aplicacion(tmp_path):
    r = _cliente_con_frontend(tmp_path).get("/alertas/5")
    assert r.status_code == 200
    assert "SPA" in r.text
