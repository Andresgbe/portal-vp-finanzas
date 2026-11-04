"""Punto de entrada de la API.

Local:       uvicorn app.main:app --reload      (desde backend/)
Producción:  la misma app sirve también el frontend compilado (frontend/dist),
             así API y web comparten dominio y no hace falta abrir CORS.
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import auth, cierres, organizacion

app = FastAPI(
    title="Portal VP de Finanzas",
    version="1.0.0",
    # La documentación interactiva (/docs) solo existe en desarrollo
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.include_router(auth.router)
app.include_router(organizacion.router)
app.include_router(cierres.router)


@app.middleware("http")
async def cabeceras_seguridad(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    if request.url.path.startswith("/api"):
        # Las respuestas con datos internos no se guardan en caché del navegador
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health", tags=["sistema"])
def health():
    return {"status": "ok"}


# ---------- Frontend compilado (solo si existe frontend/dist) ----------
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def spa(ruta: str):
        # Cualquier ruta que no sea /api la resuelve React Router
        archivo = (DIST / ruta).resolve()
        if ruta and archivo.is_file() and DIST in archivo.parents:
            return FileResponse(archivo)
        return FileResponse(DIST / "index.html")
