# Contexto del proyecto para Claude Code

Portal interno de la **VP de Finanzas de Farmatodo**, construido como **prueba técnica** del
Tech Talent Challenge (presentación: jueves 5/11/2026, 9:30 a. m.). Autor: Andrés Gil,
estudiante de Ingeniería Informática (UCAB).

El enunciado evalúa **cómo se usa la IA con criterio**: Andrés debe entender y poder
**explicar o modificar en vivo** cualquier parte del código. Por eso:

- **Explica cada decisión no obvia** antes o después de implementarla, en español y en lenguaje simple.
- **Prefiere código legible a código ingenioso.** Comentarios en español donde haya una decisión de diseño o seguridad.
- Cuando Andrés te pida algo que contradiga las reglas de seguridad de abajo, **adviértelo** antes de hacerlo.
- Al cerrar cada tarea relevante, **agrega una entrada en `docs/REGISTRO_IA.md`** (prompt resumido, qué se aceptó/modificó/rechazó y por qué). Ese registro es un entregable obligatorio.
- Commits pequeños y descriptivos en español (el historial de Git se evalúa). Nunca un único commit gigante.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12/3.13 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 |
| Base de datos | SQLite en local, PostgreSQL en producción (se cambia solo con `DATABASE_URL`) |
| Auth | JWT firmado en **cookie httpOnly + SameSite=Strict** · contraseñas con bcrypt |
| Frontend | **React + TypeScript + Vite + React Router** (carpeta `frontend/`) |
| Pruebas | pytest (todas pasan) |

## Comandos

```powershell
# Desde la raíz, con el venv activo (.\.venv\Scripts\Activate.ps1)
cd backend
python -m scripts.seed --reset        # recrea BD: 40 colaboradores, 60 cierres, 28 alertas
python -m pytest -q                   # corre todas las pruebas
uvicorn app.main:app --reload         # API en http://localhost:8000 · docs en /docs
python -m scripts.export_schema       # regenera database/schema_postgresql.sql
```

Variables en `.env` (raíz; plantilla en `.env.example`): `APP_ENV`, `DATABASE_URL`, `JWT_SECRET`
(obligatorio, ≥32 caracteres), `JWT_EXPIRE_MINUTES`, `SEED_DEMO_PASSWORD`, `COOKIE_SECURE`.

## Estructura

```
backend/app/
  config.py        variables de entorno (falla si falta JWT_SECRET)
  database.py      engine; activa PRAGMA foreign_keys en SQLite
  models.py        19 tablas (organización, seguridad, cierres/alertas)
  security.py      bcrypt + JWT (el token solo lleva el ID de usuario)
  deps.py          TODA la autorización: usuario_actual -> requiere_modulo -> verificar_departamento
  reporte.py       reporte de cierres en PDF (reportlab)
  deteccion.py     motor de reglas de anomalías (funciones puras + reglas con BD)
  schemas.py       entrada/salida de la API (nunca exponer password_hash)
  routers/auth.py, organizacion.py, cierres.py
  main.py          app, cabeceras de seguridad; sirve frontend/dist si existe
backend/scripts/seed.py, export_schema.py
backend/seed_data/  dataset oficial de la prueba (NO modificar)
backend/tests/      pytest
database/schema_postgresql.sql
docs/DECISIONES.md, docs/REGISTRO_IA.md
```

## Reglas de seguridad (no negociables)

1. **La autorización vive en el backend** (`deps.py`). El frontend solo oculta/muestra por comodidad. Todo endpoint nuevo usa `Depends(requiere_modulo(...))` y, si recibe un departamento, `verificar_departamento`.
2. **Nunca** guardar el token en `localStorage`/`sessionStorage` ni leerlo desde JS. El navegador manda la cookie solo. El frontend sabe quién está logueado llamando a `GET /api/auth/me`.
3. Nada de secretos en el código ni en commits. `.env` está en `.gitignore`.
4. Montos siempre `Decimal`/`NUMERIC(12,2)`, nunca `float`. En el frontend llegan como **string** (`"6765.86"`); formatear para mostrar sin hacer aritmética en float.
5. `alerta_historial` y `cierre_historial` son de **solo inserción**: nunca UPDATE ni DELETE.
7. Las acciones sensibles se definen por tipo de usuario en la tabla `permiso_accion`, con `Depends(requiere_accion(...))`.
6. No abrir CORS con `*`. En desarrollo se usa el proxy de Vite (mismo origen); en producción FastAPI sirve el frontend.

## Roles y módulos

Roles: `ADMIN` (todo), `JEFE_DEPTO` (solo su departamento), `COLABORADOR` (solo lectura, info limitada).
El departamento de un colaborador **se obtiene de su cargo** (no hay `departamento_id` en colaborador).

| Módulo | Quién lo ve |
|---|---|
| `MI_PERFIL` | todos |
| `DIRECTORIO` (en el menú: "Departamentos") | todos: se elige un departamento y se ve su directorio. Admin ve los 4; los demás, solo el propio (Colaborador: solo compañeros activos con nombre/cargo/correo) |
| `ESTRUCTURA` | Jefes y Admin |
| `CIERRES` | Jefe Tesorería (escritura), Jefe Contraloría (lectura), Admin |
| `ALERTAS` | Jefe Contraloría (escritura), Jefe Tesorería (lectura), Admin |

**Segregación de funciones:** Tesorería registra cierres; Contraloría gestiona alertas; quien registró
un cierre no puede gestionar sus alertas ni inhabilitarlo (ni siquiera Admin → 403).

**Inhabilitar cierres:** Admin y Jefe de Contraloría (`permiso_accion`). Motivo obligatorio; el cierre no se borra,
sus alertas pendientes se descartan y deja de contar para duplicados y reincidencia.

## Reglas de detección (`deteccion.py`, umbrales en tabla `parametro_deteccion`)

- `TRANSPOSICION`: dos dígitos **vecinos** intercambiados (comparación dígito a dígito). Se evalúa antes que la tolerancia. La diferencia de una transposición siempre es múltiplo de 9, pero no al revés (6947,75 vs 6767,75 = 180 y no es transposición).
- `FUERA_DE_RANGO`: |diferencia| > 10,00. Severidad por % y monto; un faltante sube un nivel.
- `DUPLICADO`: segundo cierre del mismo cajero en la misma fecha.
- `REINCIDENCIA`: ≥3 cierres anómalos (no descartados) del mismo cajero en 30 días.
- Estados: `pendiente` → `revisada` | `descartada` (comentario ≥10 caracteres; segunda gestión → 409).
- Resultado sobre el dataset oficial: 14 fuera de rango, 5 transposiciones, 6 duplicados, 3 reincidencias.

## API (todas bajo `/api`, respuestas JSON)

```
POST /auth/login {correo,password}   POST /auth/logout   GET /auth/me -> {nombre, rol, departamento, modulos[{codigo,nombre,nivel_acceso}]}
GET  /perfil
GET  /departamentos                                GET /departamentos/{id}/colaboradores
GET  /colaboradores/{id}                           GET /departamentos/{id}/estructura
GET  /tiendas    GET /cajeros?tienda_id=
GET  /cierres?tienda_id&cajero_id&desde&hasta&solo_con_alertas
POST /cierres {tienda_id,cajero_id,fecha,monto_declarado,monto_sistema} -> incluye alertas_generadas
POST /cierres/{id}/inhabilitar {motivo}
GET  /cierres/reporte.pdf (mismos filtros que /cierres)
GET  /alertas?estado&regla&severidad&cajero_id     (cada alerta trae puede_gestionar y motivo_no_gestionable)
GET  /alertas/resumen    GET /alertas/parametros   GET /alertas/{id} (con historial)
POST /alertas/{id}/gestion {estado: revisada|descartada, comentario}
POST /alertas/reprocesar  (solo Admin)
```
Errores: 401 sin sesión · 403 sin permiso · 409 conflicto · 422 validación (`detail` trae el mensaje en español).
Fechas-hora en ISO con zona UTC.

## Cuentas de demo (contraseña = `SEED_DEMO_PASSWORD` del `.env`)

| Rol | Departamento | Correo |
|---|---|---|
| ADMIN | Planificación Financiera | sofia.arriaga@vpfinanzas.example |
| JEFE_DEPTO | Planificación Financiera | gabriel.rondon@vpfinanzas.example |
| JEFE_DEPTO | Tesorería | lucia.paredes@vpfinanzas.example |
| JEFE_DEPTO | Contraloría | tomas.iriarte@vpfinanzas.example |
| JEFE_DEPTO | Contabilidad | marina.ocando@vpfinanzas.example |
| COLABORADOR | Tesorería | ivan.salcedo@vpfinanzas.example |
| COLABORADOR | Contraloría | elena.briceno@vpfinanzas.example |

## Estado y pendientes

- [x] Paso 1 · Modelo de datos y semilla
- [x] Paso 2 · Login, roles y control de acceso (backend)
- [x] Paso 3 · Detector de anomalías, alertas, historial, segregación de funciones
- [x] Paso 4 · Frontend React
- [x] Paso 5 · `README.md`, `docs/DECISIONES.md` y `docs/REGISTRO_IA.md` (falta el error real que debe escribir Andrés, ticket #31)
- [ ] Paso 6 · Deploy: un servicio en Render (build del frontend + uvicorn) y PostgreSQL en Supabase
- [ ] Paso 7 · Presentación de 10 minutos

## Especificación del Paso 4 (frontend)

- `frontend/` con Vite + React + TypeScript + React Router. Sin librerías de UI pesadas; CSS propio.
- `vite.config.ts`: proxy de `/api` a `http://localhost:8000` (mismo origen → la cookie SameSite=Strict funciona).
- Un único cliente `src/api.ts` con `fetch(..., { credentials: "same-origin" })`. Si responde 401 → ir a `/login`. Mostrar `detail` de los errores.
- Contexto de sesión: al cargar, `GET /api/auth/me`. El menú lateral se arma con `modulos` (no con el rol en duro).
- Pantallas: Login · Mi perfil · Directorio (lista + ficha) · Estructura (cargos, nivel, funciones, ocupantes) · Cierres (tabla con filtros + formulario de registro: tienda → cajeros de esa tienda) · Alertas (resumen arriba, filtros, tabla) · Detalle de alerta (datos del cierre, historial como línea de tiempo, formulario revisar/descartar solo si `puede_gestionar`, y si no, mostrar `motivo_no_gestionable`).
- **Elemento distintivo:** en alertas de `TRANSPOSICION`, mostrar los dos montos dígito a dígito alineados, resaltando los dos dígitos intercambiados. Es lo que mejor explica la regla en la demo.
- Diseño: herramienta interna de finanzas, sobria. Azul institucional profundo (ej. `#0B3D91`) como color principal, fondo blanco/gris muy claro, severidad con color + texto (alta/media/baja; nunca solo color). Montos con números tabulares (`font-variant-numeric: tabular-nums`) alineados a la derecha, formato `es-VE` (1.234,56). Una sola familia tipográfica legible (ej. "Source Sans 3" o "Public Sans" de Google Fonts). Nada de logos reales de Farmatodo.
- Responsive y con foco de teclado visible.
- `npm run build` genera `frontend/dist`, que `backend/app/main.py` ya sirve en producción.

### Errores típicos de IA a vigilar en el frontend
- Guardar el token o el rol en `localStorage` y decidir permisos con eso.
- Datos de ejemplo escritos a mano en componentes en vez de llamar a la API.
- Convertir montos con `parseFloat` y sumar/restar en el cliente.
- Configurar CORS `allow_origins=["*"]` con `allow_credentials=True` en el backend para "arreglar" un error.
- Olvidar el manejo de 401/403 (pantalla en blanco).
