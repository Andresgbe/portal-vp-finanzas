# Portal VP de Finanzas · Detector de anomalías en cierres de caja

Portal interno para la Vicepresidencia de Finanzas: estructura organizacional, acceso por rol y
departamento, y un proceso de negocio completo de **detección y gestión de anomalías en cierres de caja**.

Prueba técnica · Farmatodo Tech Talent Challenge · Andrés Gil.

- Decisiones técnicas: [`docs/DECISIONES.md`](docs/DECISIONES.md)
- Registro de uso de IA: [`docs/REGISTRO_IA.md`](docs/REGISTRO_IA.md)
- Modelo de datos (DDL): [`database/schema_postgresql.sql`](database/schema_postgresql.sql)

## Requisitos
- Python 3.12 o 3.13
- Node.js 20 o superior (frontend)
- Git

## Levantar el backend

```powershell
# 1. Entorno virtual y dependencias (desde la raíz del proyecto)
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Mac/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt

# 2. Variables de entorno
copy .env.example .env                 # Mac/Linux: cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
#    -> pega el resultado en JWT_SECRET y define SEED_DEMO_PASSWORD (mín. 10 caracteres)

# 3. Base de datos con datos ficticios
cd backend
python -m scripts.seed --reset

# 4. Pruebas y servidor
python -m pytest -q
uvicorn app.main:app --reload          # http://localhost:8000/docs
```

## Levantar el frontend
*(Paso 4: pendiente)*

## Variables de entorno

| Variable | Descripción |
|---|---|
| `APP_ENV` | `development` o `production` |
| `DATABASE_URL` | `sqlite:///./portal.db` en local; `postgresql+psycopg://...` en producción |
| `JWT_SECRET` | Clave para firmar sesiones. Obligatoria, mínimo 32 caracteres |
| `JWT_EXPIRE_MINUTES` | Duración de la sesión (por defecto 60) |
| `SEED_DEMO_PASSWORD` | Contraseña de los usuarios de demostración |
| `COOKIE_SECURE` | `true` en producción (HTTPS) |

## Cuentas de demostración
Contraseña: el valor de `SEED_DEMO_PASSWORD`.

| Rol | Departamento | Correo |
|---|---|---|
| Administrador | Planificación Financiera | sofia.arriaga@vpfinanzas.example |
| Jefe | Tesorería (registra cierres) | lucia.paredes@vpfinanzas.example |
| Jefe | Contraloría (gestiona alertas) | tomas.iriarte@vpfinanzas.example |
| Jefe | Contabilidad | marina.ocando@vpfinanzas.example |
| Colaborador | Tesorería | ivan.salcedo@vpfinanzas.example |

Todos los datos son ficticios.
