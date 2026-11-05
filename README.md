# Portal VP de Finanzas

Portal interno con control de acceso por rol y un proceso completo de detección y gestión de anomalías en cierres de caja. Prueba técnica de Andrés Gil para el Tech Talent Challenge de Farmatodo. **Todos los datos son ficticios.**

## Cuentas

La contraseña de todas es el valor de `SEED_DEMO_PASSWORD` en el archivo `.env`.

| Rol | Correo | Qué puede hacer |
|---|---|---|
| **Administrador** | `sofia.arriaga@vpfinanzas.example` | Ve los 4 departamentos y todos los módulos |
| **Jefe de Departamento** (Contraloría) | `tomas.iriarte@vpfinanzas.example` | Ve solo su departamento, consulta cierres y gestiona alertas |
| **Colaborador** (Tesorería) | `ivan.salcedo@vpfinanzas.example` | Solo lectura: su perfil y sus compañeros activos, con datos limitados |

Para registrar cierres en la demo: `lucia.paredes@vpfinanzas.example`, Jefe de Tesorería.

## Ejecutar

Requiere Python 3.12 o 3.13 y Node.js 20 o superior. Se usan **dos terminales**, ambas desde la raíz del proyecto.

**Terminal 1: backend**

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload
```

**Terminal 2: frontend**

```powershell
cd frontend
npm run dev
```

Abrir **http://localhost:5173**.

### Primera instalación

Se hace una sola vez, antes de lo anterior:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Pegar el resultado en `JWT_SECRET` dentro de `.env` y definir `SEED_DEMO_PASSWORD` (mínimo 10 caracteres). Luego:

```powershell
cd backend
python -m scripts.seed --reset
cd ..\frontend
npm install
```

## Antes de presentar

Deja la base limpia. **Esto borra lo creado en pruebas anteriores.**

```powershell
cd backend
python -m scripts.seed --reset
```

Si la aplicación se comporta raro tras un cambio, recarga con `Ctrl + F5`.

## Recorrido de la demo

1. **Sofía:** abre Departamentos y muestra los 4.
2. **Lucía:** en Cierres registra `1.520,00` contra `1.250,00`. Se genera una alerta de transposición. Al abrirla, no puede gestionarla.
3. **Tomás:** en Alertas abre esa alerta, ve los dígitos resaltados y la marca como revisada. Queda en el historial.
4. **Iván:** escribe `/alertas` en la dirección y recibe "No tienes acceso a este módulo".

Otros puntos para mostrar:

- **Alerta #8:** 3.954,90 contra 3.945,90. Difiere solo 9,00, así que la tolerancia no la habría detectado.
- **Inhabilitar un cierre:** Tomás, en Cierres, con motivo obligatorio.
- **Descargar PDF:** en Cierres, respeta los filtros activos.

## Datos a la mano

| Dato | Valor |
|---|---|
| Departamentos | Contabilidad 9, Contraloría 10, Planificación Financiera 11, Tesorería 10 (40 colaboradores) |
| Cierres y alertas | 60 cierres, 28 alertas: 14 fuera de rango, 6 duplicados, 5 transposiciones, 3 reincidencias |
| Base de datos | SQLite en local, 19 tablas. PostgreSQL está preparado, pero sin probar ni desplegar |
| Pruebas | Backend: `python -m pytest -q` desde `backend/`. Frontend: `npm test` desde `frontend/` |
| Repositorio | https://github.com/Andresgbe/portal-vp-finanzas |

**Regla clave:** quien registra un cierre no puede gestionar sus alertas ni inhabilitarlo, ni siquiera el Administrador. Los permisos se validan en el backend, no en la pantalla.

## Documentación

- [Decisiones técnicas](docs/DECISIONES.md): stack, modelo de datos, seguridad y limitaciones.
- [Registro de uso de IA](docs/REGISTRO_IA.md)
- [Modelo de datos (DDL)](database/schema_postgresql.sql)
- [`.env.example`](.env.example): variables de entorno necesarias.
