# Contexto del proyecto

Resumen para retomar el trabajo en cualquier chat o sesión. Actualizado el 3 de noviembre de 2026.

Este archivo cubre el proceso, el enunciado y el estado actual. Lo técnico está en otros documentos:

| Documento | Contenido |
|---|---|
| [`CLAUDE.md`](../CLAUDE.md) | Stack, comandos, API, reglas de seguridad, cuentas de demo y especificación del frontend |
| [`ARQUITECTURA.md`](ARQUITECTURA.md) | Capas, prácticas de ingeniería, diagnóstico del backend y plan de ejecución |
| [`DECISIONES.md`](DECISIONES.md) | Justificación del stack, modelo de datos, reglas de detección y limitaciones |
| [`REGISTRO_IA.md`](REGISTRO_IA.md) | Prompts principales, sugerencias aceptadas o rechazadas y errores detectados |

## 1. Qué es

Portal interno para la Vicepresidencia de Finanzas de Farmatodo, construido como prueba técnica del **Tech Talent Challenge**, parte del proceso de selección del programa de pasantías. El candidato es Andrés Gil, estudiante de Ingeniería Informática (UCAB).

La prueba evalúa **cómo se usa la IA con criterio**, no si se usó. Pueden pedir explicar o modificar en vivo cualquier parte del código.

## 2. El evento

- **Cuándo:** jueves 5 de noviembre de 2026, 9:30 a. m.
- **Dónde:** C. C. Expreso Baruta. Preguntar por Daniela Plata en recepción.

| Parte | Tiempo | Contenido |
|---|---|---|
| 1. Presentación personal y académica | 3 a 5 min (se puede llevar una lámina) | Qué estudias, dónde estudias, qué te apasiona y qué esperas de las pasantías en Farmatodo |
| 2. Caso de negocio y propuesta | 10 min | Cómo desarrollaste la propuesta: análisis, ideas y soluciones al caso |

## 3. Lo que exige el enunciado

Fuente: `Enunciado_Prueba_Tecnica_Candidato.pdf`.

| Requisito | Estado |
|---|---|
| Base de datos relacional normalizada, con al menos 4 departamentos | Hecho |
| 8 a 12 colaboradores ficticios por departamento | Hecho: Contabilidad 9, Contraloría 10, Planificación 11, Tesorería 10 |
| Login real y roles Administrador, Jefe y Colaborador, validados en el backend | Hecho |
| Al menos 3 módulos visibles según el rol | API lista, **faltan las pantallas** |
| Un proceso de negocio completo: detector de anomalías en cierres de caja | API lista, **faltan las pantallas** |
| **Frontend con framework que consuma la API real** | **Pendiente** |
| Secretos en `.env` y `.gitignore` correcto | Hecho |
| Historial de Git que refleje el avance | Hecho: 8 commits |
| README con instrucciones para levantar el proyecto | Parcial: falta el frontend |
| Documento de decisiones | Parcial: falta la sección del frontend y el deploy |
| Registro de IA con al menos un error real detectado | Parcial: **falta la sección "Error que detecté yo"** |

## 4. Decisiones ya tomadas

- **Caso:** cierres de caja, no notas de crédito. Tiene más lógica de negocio, y el dataset de notas de crédito contradice al enunciado sobre registrar quién aprueba.
- **Stack:** FastAPI + React. El criterio principal fue la facilidad de desplegar: un solo servicio sirve la API y el frontend.
- **Base de datos:** SQLite en local y PostgreSQL en Supabase en producción. El plan gratuito de Render borra su Postgres a los 30 días y pierde los archivos SQLite al reiniciar.
- **Forma de trabajo:** paso a paso, explicando cada decisión no obvia antes o después de implementarla.

## 5. Historia del trabajo

1. En **claude.ai** se analizaron el enunciado y los datos, y se construyó el backend (pasos 1 a 3).
2. Ese trabajo salió de allí como un **git bundle**: `Downloads/portal-completo.bundle`.
3. El 3 de noviembre de 2026 se integró al repo local con `git pull --ff-only`, sin divergencias.
4. El trabajo sigue en **Claude Code**, dentro de VS Code, a partir del paso 4.

## 6. Estado verificado (3 de noviembre de 2026)

- Ramas `master` (deploy) y `dev` (trabajo diario). Los cambios pasan de `dev` a `master` con un pull request.
- `python -m pytest -q`: **60 pruebas pasan**.
- La detección da 14 fuera de rango, 5 transposiciones, 6 duplicados y 3 reincidencias. Una prueba lo comprueba.
- Python 3.12.10 y Node 24.20.0 instalados.
- Repositorio público: `github.com/Andresgbe/portal-vp-finanzas`. El trabajo se sigue con tickets, un milestone por fase del SDLC y un tablero de GitHub Projects.
- **`backend/portal.db` está desactualizada:** tiene 0 alertas porque es anterior al paso 3. Se corrige con `python -m scripts.seed --reset`, desde `backend/`.

## 7. Qué falta, en orden

1. **Paso 4: frontend React.** Es lo único obligatorio sin empezar. La especificación está en `CLAUDE.md`.
2. **Paso 5: documentación.** Completar README, DECISIONES y REGISTRO_IA.
3. **Error real detectado:** Andrés debe escribirlo con algo que haya notado personalmente. No se puede inventar ni delegar a la IA.
4. **Tickets y tablero:** mantenerlos al día mientras se avanza.
5. **Paso 6: deploy** en Render y Supabase. Es opcional: el enunciado solo pide poder levantarlo localmente.
6. **Paso 7: presentación.** Una lámina personal y 10 minutos sobre el caso.
7. **Ensayo:** practicar la explicación y la modificación en vivo del código.

## 8. Material de origen

Todo está en la carpeta `Downloads` de Andrés:

- `Enunciado_Prueba_Tecnica_Candidato.pdf`
- `datas_candidato.zip`: datasets. El de cierres ya está en `backend/seed_data/`.
- `Tech Talent Challenge 2026 Farmatodo.png` e `Infografía Tech Talent Challenge de Farmatodo.png`: láminas del evento.
- `portal-completo.bundle`: ya integrado, se puede conservar como respaldo.
