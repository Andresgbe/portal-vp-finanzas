# Registro de uso de Inteligencia Artificial

Herramientas utilizadas:
- **Claude (claude.ai):** análisis del enunciado y de los datos, diseño del modelo y desarrollo del backend (Pasos 1 a 3).
- **Claude Code (extensión de VS Code):** frontend, documentación y deploy (Pasos 4 en adelante).

Forma de trabajo: el proyecto se dividió en pasos y la IA presentó cada decisión de diseño antes de implementarla. Cada commit tiene la línea `Co-Authored-By: Claude`, de modo que el historial de Git muestra con transparencia qué se hizo con IA.

---

## 1. Prompts principales

### Prompt 1: Arranque (claude.ai)
> *[Adjunté el PDF del enunciado, el ZIP con los datasets y las dos láminas del evento]*
> "Quiero hacerlo muy bien porque es para una entrevista de trabajo en Farmatodo."

**Resultado:** antes de proponer nada, la IA analizó los datasets y encontró:
- transposiciones de dígitos sembradas en los cierres;
- 6 casos del mismo cajero con dos cierres en la misma fecha, aunque el README dice que hay uno por día;
- una contradicción entre el enunciado y el README de notas de crédito sobre registrar o no quién aprueba.

Luego me hizo tres preguntas: qué caso construir, qué stack usar y cómo trabajar.

### Prompt 2: Elección de caso, stack y forma de trabajo
> Elegí: **Cierres de caja**. Ante la pregunta del stack respondí: **"¿Cuál es más fácil para hacer deploy y subir?"**. Forma de trabajo: **paso a paso juntos**.

**Decisión:** Python (FastAPI) + React. La razón que pesó fue la del deploy: un solo servicio que sirve API y frontend, con PostgreSQL en Supabase. El plan gratuito de Render borra su Postgres a los 30 días y pierde los archivos SQLite en cada reinicio.

### Prompt 3: Modelo de datos
La IA propuso el modelo y las reglas calibradas con los datos. Respondí: **"Ok, empieza el proyecto"**.

### Prompt 4: Trabajo local
> "Dame el comando para crear el proyecto desde Visual" / "Lo haré con la extensión de Claude Code, dame el contexto."

**Resultado:** se generó `CLAUDE.md` con el contexto, las reglas de seguridad y la especificación del frontend, para continuar en VS Code.

### Prompt 5: Traer el trabajo a local y guardar el contexto (Claude Code)
> *[Adjunté el enunciado, las láminas del evento y `CLAUDE.md`]* "Crea un MD y guarda el contexto. Tengo un archivo bundle pero no sé cómo exportarlo."

**Resultado:** la IA verificó el bundle antes de usarlo y confirmó que continuaba el historial local. Lo integró con `git pull --ff-only`, corrió las pruebas (60 pasan) y creó `docs/CONTEXTO_PROYECTO.md`, que compara el enunciado con el estado real del proyecto.

### Prompt 6: Arquitectura y buenas prácticas antes del frontend (Claude Code)
> "Antes de empezar el front, dime buenas prácticas y cómo deberíamos abordar este proyecto para que tenga la arquitectura y buenas prácticas de ingeniería de software."

**Resultado:** la IA revisó el backend y ejecutó pruebas sobre una copia aislada. Encontró que los errores 422 no cumplían el formato documentado, que `/api/no-existe` respondía 200 con HTML y que un `APP_ENV` mal escrito desactivaba las protecciones de producción. El plan quedó en `docs/ARQUITECTURA.md`. Descartó microservicios y arquitectura hexagonal por desproporcionados.

### Prompt 7: Planificación en GitHub según el SDLC (Claude Code)
> *[Adjunté una imagen con las 7 fases]* "Nos guiaremos bajo estas 7 fases. Yo quiero crear dos ramas, una dev y otra que es la master, donde haremos el deploy, y ayúdame a crear la sección de issues."

**Resultado:** se crearon las ramas `master` y `dev`, un milestone por fase, etiquetas, tickets y un tablero. La IA señaló que la imagen decía "SDCL" en vez de SDLC, y que los tickets del trabajo ya hecho debían quedar marcados como `retroactivo` y no presentarse como planificación previa.

### Prompt 8: Diseño e interfaz (Claude Code)
> "Usemos Claude Design, que sea una plataforma consistente, moderna e intuitiva, sin colores que sobresalgan." Luego: "Que el login tenga ver contraseña y fondo tipo glass" y "moderniza más las otras vistas".

**Resultado:** se diseñaron las vistas en un lienzo con datos ficticios de la semilla, se iteró dos veces y se implementaron en React. Se verificó en un navegador real con login por la interfaz, con tres cuentas (Contraloría, Tesorería y Colaborador), y el recorrido de la demo contra la API. La IA dejó el vidrio más opaco en las pantallas con montos para que se pudieran leer.

### Prompt 9: Pestaña de departamentos (Claude Code)
> "No veo los departamentos, y quiero una pestaña extra que los muestre."

**Resultado:** se agregó el módulo `DEPARTAMENTOS` desde el backend, para que el menú siga saliendo de la API y no de un rol escrito en el frontend. El Administrador ve los 4 departamentos y los demás roles solo el propio, como pide el enunciado; hay una prueba que lo verifica.

### Prompt 10: Unir departamentos y directorio (Claude Code)
> "No veo los departamentos. En vez de Directorio, ¿por qué no pones Departamento y que cada departamento, al seleccionarlo, muestre el directorio?"

**Decisión mía:** cambié la navegación que había propuesto la IA, que tenía dos pestañas separadas con filtros. Ahora hay una sola pestaña: Departamentos lleva al directorio de cada uno. El alcance por rol sigue validándose en el backend.

### Prompt 11: Inhabilitar cierres (Claude Code)
> "Que me deje inhabilitar transacciones. Recuerda que hay distintos tipos de usuarios; define eso en la BD."

**Resultado:** la IA advirtió el riesgo de que quien registra pudiera esconder un faltante y preguntó quién debía poder hacerlo. Elegí Contraloría y Admin, nunca quien registró el cierre, y que las alertas pendientes se descartaran. Se crearon `permiso_accion` y `cierre_historial`; una prueba confirma que quitar la fila de la base de datos quita el permiso.

### Prompt 12: Reporte en PDF (Claude Code)
> "Dame la opción de poder descargar el reporte en PDF."

**Resultado:** el PDF se genera en el backend con los mismos permisos y filtros que la tabla. Como el motivo de inhabilitación lo escribe un usuario, se escapa antes de ponerlo en el PDF, y una prueba lo comprueba.

<!-- Agrega aquí los prompts importantes que uses en Claude Code (frontend, deploy...) -->

---

## 2. Sugerencias aceptadas, modificadas y rechazadas

| Sugerencia de la IA | Decisión | Por qué |
|---|---|---|
| Caso de cierres de caja en vez de notas de crédito | Aceptada | Tiene más lógica de negocio y el de notas de crédito trae una contradicción sin resolver. |
| Python + React | Aceptada, con mi criterio de deploy | Pregunté cuál era más fácil de desplegar; esa fue la razón de la elección. |
| Separar funciones: Tesorería registra y Contraloría revisa | Aceptada | Es un control interno real de finanzas. |
| Cierres duplicados como alerta, no como rechazo | Aceptada | No sabemos si existen turnos dobles; rechazarlos perdería información. |
| JWT en cookie httpOnly | Aceptada | Ver la sección 3. |
| Dos pestañas (Departamentos y Directorio) con filtros | Modificada | Yo pedí una sola pestaña: se elige el departamento y aparece su directorio. Es más clara. |
| Tesorería podría inhabilitar cierres | Rechazada | La IA presentó las opciones; elegí Contraloría y Admin porque Tesorería registra y podría ocultar un faltante. |
| Regla de quién puede inhabilitar | Modificada | Pedí que quedara definida en la base de datos, por tipo de usuario. Se creó la tabla `permiso_accion`. |

---

## 3. Errores o malas prácticas detectados en respuestas de IA

### Práctica común rechazada: token en `localStorage`
Muchas guías y asistentes de IA guardan el JWT en `localStorage` y lo envían en un header. Es vulnerable: cualquier script inyectado (XSS) puede leerlo y robar la sesión. Se usa una cookie **httpOnly + SameSite=Strict**, que JavaScript no puede leer.

### Correcciones durante el desarrollo
Se encontraron al revisar el código y al correr las pruebas, y se corrigieron antes de cada commit:
1. **Llaves foráneas desactivadas en SQLite.** SQLite no valida FKs si no se activa `PRAGMA foreign_keys`. Se verificó insertando un cierre con un cajero inexistente (rechazado) y se dejó activado en `database.py`.
2. **Orden de seniority frágil.** Una consulta ordenaba por `nivel_id`, suponiendo que los IDs seguían el orden de los niveles. Se cambió a `nivel.orden`, que es el dato real.
3. **Pruebas que dependían del orden de ejecución.** Algunas pruebas modificaban datos que otras leían. Se aislaron recreando la BD (fixture `bd_limpia`).
4. **Dependencia oculta.** Se importó `EmailStr` de Pydantic, que requiere un paquete extra no instalado. Se quitó.
5. **Fechas sin zona horaria.** SQLite devolvía fechas sin zona y el navegador las habría mostrado 4 horas corridas. Se marcan como UTC al responder.
6. **Errores 422 que repetían lo enviado.** Además de venir en inglés, incluían el campo `input`, que podía contener una contraseña. Se reemplazaron por un mensaje en español sin ese dato.
7. **Prueba que no probaba nada.** La IA escribió una prueba de salida de carpeta (`/%2e%2e/...`), pero el cliente de pruebas normaliza la URL, así que pasaría con o sin protección. Se eliminó en vez de dejar una falsa seguridad.

### Error que detecté yo
<!--
  OBLIGATORIO según la sección 5 del enunciado. Debe ser real: algo que TÚ notaste.
  Formato sugerido:
  - Qué le pedí a la IA:
  - Qué respondió (el problema):
  - Cómo lo detecté:
  - Cómo lo corregí:
-->
