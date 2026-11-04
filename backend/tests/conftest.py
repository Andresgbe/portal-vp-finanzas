"""Configuración de las pruebas: cada sesión de tests usa su propia BD temporal."""
import os
import tempfile
from pathlib import Path

# Las variables se definen ANTES de importar la app (la config se lee al importar)
_tmp = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}"
os.environ["JWT_SECRET"] = "clave-solo-para-pruebas-" + "x" * 32
os.environ["SEED_DEMO_PASSWORD"] = "Prueba.12345"
os.environ["APP_ENV"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.security import hash_password  # noqa: E402
from scripts.seed import cargar_cierres, cargar_organizacion  # noqa: E402

PASSWORD = "Prueba.12345"
CUENTAS = {
    "admin": "sofia.arriaga@vpfinanzas.example",
    "jefe_planificacion": "gabriel.rondon@vpfinanzas.example",
    "jefe_tesoreria": "lucia.paredes@vpfinanzas.example",
    "jefe_contraloria": "tomas.iriarte@vpfinanzas.example",
    "jefe_contabilidad": "marina.ocando@vpfinanzas.example",
    "colab_tesoreria": "ivan.salcedo@vpfinanzas.example",
    "colab_contraloria": "elena.briceno@vpfinanzas.example",
}


def _sembrar():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        cargar_organizacion(db, hash_password(PASSWORD))
        cargar_cierres(db)
        db.commit()


@pytest.fixture(scope="session", autouse=True)
def base_de_datos():
    _sembrar()
    yield


@pytest.fixture
def bd_limpia():
    """Para tests que modifican datos y necesitan empezar desde cero."""
    _sembrar()
    yield


@pytest.fixture
def cliente():
    return TestClient(app)


@pytest.fixture
def login():
    """login("jefe_tesoreria") -> TestClient con la cookie de sesión puesta."""
    def _login(quien: str) -> TestClient:
        c = TestClient(app)
        r = c.post("/api/auth/login", json={"correo": CUENTAS[quien], "password": PASSWORD})
        assert r.status_code == 200, r.text
        return c
    return _login
