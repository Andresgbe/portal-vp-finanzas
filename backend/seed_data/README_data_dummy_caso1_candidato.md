# Data de ejemplo — Caso 1: Detector de anomalías en cierres de caja

Este archivo contiene un dataset de ejemplo que puedes usar como semilla para tu base de datos.
**Es completamente opcional**: puedes usarlo tal cual, adaptarlo, o generar tu propia data
ficticia con AI o scripts — lo que se evalúa es el modelo relacional y la lógica que construyas
encima, no el origen de los datos.

## Qué contiene

| Tabla | Registros | Descripción |
|---|---|---|
| `tiendas` | 6 | Tiendas ficticias en Venezuela y Argentina. |
| `cajeros` | 12 | Cajeros ficticios, cada uno asignado a una tienda. |
| `cierres_caja` | 60 | Un cierre de caja por cajero/fecha, con el monto que declaró (`monto_declarado`) frente al monto que registró el sistema (`monto_sistema`). |

## Sobre los datos

Algunos de los 60 cierres tienen diferencias entre `monto_declarado` y `monto_sistema` — otros
no. Sobre esa comparación debes construir tu propia lógica de detección de anomalías, según lo
descrito en la Opción 1 de la sección 3.4 del enunciado (diferencias fuera de rango, sospecha de
transposición de dígitos, reincidencia de un mismo cajero, etc.).

No incluimos ninguna tabla de alertas ya resuelta — ese es justamente el resultado que tu
sistema debe generar.

## Cómo usarlo

```bash
# SQLite
sqlite3 mi_base.db < data_dummy_cierres_caja_candidato.sql

# PostgreSQL
psql -U usuario -d mi_base -f data_dummy_cierres_caja_candidato.sql
```

Si prefieres otro motor de base de datos, puedes adaptar los tipos de dato del `CREATE TABLE`
que incluye el script — están escritos en SQL estándar para que sea fácil de portar.

## Una aclaración importante

Este dataset cubre solo la parte de tiendas/cajeros/cierres de caja del ejercicio. El resto del
portal (login, roles, departamentos de la VP de Finanzas) lo debes diseñar tú, según la sección
3 del enunciado general de la prueba.
