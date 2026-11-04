"""Exporta el DDL (CREATE TABLE) del modelo a database/schema_postgresql.sql.

El modelo vive en app/models.py; este archivo SQL es la versión legible
para revisar tablas, llaves y restricciones sin leer Python.

Uso (desde backend/):  python -m scripts.export_schema
"""
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.database import Base
from app import models  # noqa: F401  (registra las tablas)

OUT = Path(__file__).resolve().parents[2] / "database" / "schema_postgresql.sql"


def main() -> None:
    dialect = postgresql.dialect()
    partes = ["-- Generado desde backend/app/models.py con scripts/export_schema.py",
              "-- Motor: PostgreSQL. Los datos semilla se cargan con scripts/seed.py\n"]
    for table in Base.metadata.sorted_tables:
        partes.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";\n")
        for idx in sorted(table.indexes, key=lambda i: i.name):
            partes.append(str(CreateIndex(idx).compile(dialect=dialect)).strip() + ";\n")
    OUT.write_text("\n".join(partes), encoding="utf-8")
    print(f"Escrito {OUT}")


if __name__ == "__main__":
    main()
