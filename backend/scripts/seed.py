"""Crea las tablas y carga datos 100 % ficticios.

Uso (desde la carpeta backend/):
    python -m scripts.seed --reset

--reset borra y vuelve a crear todas las tablas. Por seguridad, el script
se niega a correr con APP_ENV=production salvo que se pase --force-production.
"""
import argparse
import random
import sqlite3
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.deteccion import reprocesar_todo
from app.models import (
    Cajero, Cargo, CierreCaja, Colaborador, Departamento, Funcion, Modulo,
    Nivel, Pais, ParametroDeteccion, PermisoAccion, PermisoModulo, Rol, Tienda, Usuario,
)
from app.security import hash_password

SEED_DIR = Path(__file__).resolve().parents[1] / "seed_data"
DATASET_CIERRES = SEED_DIR / "data_dummy_cierres_caja_candidato.sql"
DOMINIO = "vpfinanzas.example"  # dominio reservado: nunca será un correo real

rng = random.Random(2026)  # semilla fija: mismos datos en cada ejecución

# ---------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------
PAISES = [("Venezuela", "VE"), ("Colombia", "CO"), ("Argentina", "AR")]

NIVELES = [("Analista Junior", 1), ("Analista", 2), ("Analista Senior", 3),
           ("Coordinador", 4), ("Gerente", 5)]

DEPARTAMENTOS = {
    "Planificación Financiera": "Presupuesto, proyecciones y seguimiento de la gestión financiera.",
    "Tesorería": "Manejo de efectivo, flujo de caja, bancos y custodia de valores de tiendas.",
    "Contraloría": "Control interno, auditoría de tiendas y prevención de pérdidas.",
    "Contabilidad": "Registro contable, cierres mensuales y estados financieros.",
}

# departamento -> [(cargo, nivel, [funciones])]
COMUN_GERENTE = "Liderar al equipo y responder por los resultados del departamento"
COMUN_REPORTES = "Elaborar reportes de gestión para la Vicepresidencia"
CARGOS = {
    "Planificación Financiera": [
        ("Gerente de Planificación Financiera", "Gerente", [COMUN_GERENTE, "Aprobar el presupuesto anual de la VP", COMUN_REPORTES]),
        ("Administrador del Portal Financiero", "Coordinador", ["Administrar usuarios y permisos del portal", "Velar por la calidad de los datos del portal"]),
        ("Coordinador de Presupuesto", "Coordinador", ["Consolidar el presupuesto por unidad de negocio", "Hacer seguimiento real vs. presupuesto"]),
        ("Analista Senior de Planificación", "Analista Senior", ["Construir modelos de proyección financiera", COMUN_REPORTES]),
        ("Analista de Presupuesto", "Analista", ["Cargar y validar partidas presupuestarias", "Preparar análisis de variaciones"]),
        ("Analista Junior de Planificación", "Analista Junior", ["Actualizar bases de datos de indicadores", "Apoyar en la preparación de reportes"]),
    ],
    "Tesorería": [
        ("Gerente de Tesorería", "Gerente", [COMUN_GERENTE, "Gestionar la liquidez y relación con bancos", "Supervisar los cierres de caja de tiendas"]),
        ("Coordinador de Flujo de Caja", "Coordinador", ["Proyectar el flujo de caja semanal", "Coordinar traslados de valores"]),
        ("Analista Senior de Tesorería", "Analista Senior", ["Conciliar depósitos de tiendas con bancos", COMUN_REPORTES]),
        ("Analista de Conciliaciones Bancarias", "Analista", ["Conciliar movimientos bancarios diarios", "Registrar cierres de caja recibidos de tiendas"]),
        ("Analista Junior de Tesorería", "Analista Junior", ["Archivar soportes de depósitos", "Apoyar en conciliaciones"]),
    ],
    "Contraloría": [
        ("Gerente de Contraloría", "Gerente", [COMUN_GERENTE, "Definir el plan anual de auditoría", "Resolver alertas de anomalías de caja"]),
        ("Coordinador de Auditoría de Tiendas", "Coordinador", ["Planificar visitas de auditoría a tiendas", "Dar seguimiento a hallazgos"]),
        ("Analista Senior de Control Interno", "Analista Senior", ["Evaluar controles de procesos críticos", "Investigar diferencias de caja"]),
        ("Analista de Control Interno", "Analista", ["Revisar alertas de anomalías de caja", COMUN_REPORTES]),
        ("Analista Junior de Auditoría", "Analista Junior", ["Recolectar evidencias de auditoría", "Apoyar en arqueos de caja"]),
    ],
    "Contabilidad": [
        ("Gerente de Contabilidad", "Gerente", [COMUN_GERENTE, "Firmar los estados financieros", COMUN_REPORTES]),
        ("Coordinador de Cierre Contable", "Coordinador", ["Coordinar el cierre contable mensual", "Revisar asientos de ajuste"]),
        ("Contador Senior", "Analista Senior", ["Preparar estados financieros", "Atender a auditores externos"]),
        ("Analista Contable", "Analista", ["Registrar asientos contables", "Conciliar cuentas contables"]),
        ("Analista Contable Junior", "Analista Junior", ["Registrar facturas de proveedores", "Apoyar en conciliaciones contables"]),
    ],
}

# Cuántas personas ocupan cada cargo (por posición en la lista de arriba)
DOTACION = {
    "Planificación Financiera": [1, 1, 1, 2, 3, 3],  # 11
    "Tesorería": [1, 1, 2, 3, 3],                     # 10
    "Contraloría": [1, 1, 2, 3, 3],                   # 10
    "Contabilidad": [1, 1, 2, 3, 2],                  # 9
}

# Personas fijas (para que las cuentas de demo sean estables y documentables)
PERSONAS_FIJAS = {
    ("Planificación Financiera", "Gerente de Planificación Financiera"): ("Gabriel", "Rondón"),
    ("Planificación Financiera", "Administrador del Portal Financiero"): ("Sofía", "Arriaga"),
    ("Tesorería", "Gerente de Tesorería"): ("Lucía", "Paredes"),
    ("Contraloría", "Gerente de Contraloría"): ("Tomás", "Iriarte"),
    ("Contabilidad", "Gerente de Contabilidad"): ("Marina", "Ocando"),
}
COLABORADORES_DEMO = {"Tesorería": ("Iván", "Salcedo"), "Contraloría": ("Elena", "Briceño")}

NOMBRES = ["Andrea", "Luis", "María", "Carlos", "Paola", "José", "Valentina", "Diego",
           "Camila", "Jorge", "Isabel", "Ricardo", "Natalia", "Fernando", "Gabriela",
           "Pedro", "Mariana", "Héctor", "Claudia", "Rafael", "Verónica", "Sebastián",
           "Carolina", "Manuel", "Alejandra", "Óscar", "Patricia", "Eduardo", "Lorena",
           "Mateo", "Adriana", "Simón", "Rebeca", "Nicolás", "Daniela", "Gustavo"]
APELLIDOS = ["Mendoza", "Rivas", "Guerrero", "Linares", "Carrasco", "Zambrano", "Peña",
             "Medina", "Quintero", "Aponte", "Salazar", "Villegas", "Toro", "Escalante",
             "Barrios", "Montilla", "Urdaneta", "Graterol", "Acosta", "Pacheco", "Lugo",
             "Ferrer", "Molina", "Rangel", "Vivas", "Sosa", "Cordero", "Herrera"]

MODULOS = [
    ("MI_PERFIL", "Mi perfil", "Tus datos, tu cargo y tus funciones.", 1),
    ("DIRECTORIO", "Departamentos", "Departamentos de la VP de Finanzas y su directorio.", 2),
    ("ESTRUCTURA", "Estructura organizacional", "Cargos, niveles y funciones por departamento.", 3),
    ("CIERRES", "Cierres de caja", "Registro y consulta de cierres de caja de tiendas.", 4),
    ("ALERTAS", "Alertas de anomalías", "Gestión de alertas detectadas en los cierres de caja.", 5),
]

# (módulo, rol, departamento o None = cualquiera, nivel)
PERMISOS = [
    ("MI_PERFIL", "JEFE_DEPTO", None, "lectura"),
    ("MI_PERFIL", "COLABORADOR", None, "lectura"),
    ("DIRECTORIO", "JEFE_DEPTO", None, "lectura"),
    ("DIRECTORIO", "COLABORADOR", None, "lectura"),
    ("ESTRUCTURA", "JEFE_DEPTO", None, "lectura"),
    # Segregación de funciones: Tesorería registra cierres, Contraloría gestiona alertas
    ("CIERRES", "JEFE_DEPTO", "Tesorería", "escritura"),
    ("CIERRES", "JEFE_DEPTO", "Contraloría", "lectura"),
    ("ALERTAS", "JEFE_DEPTO", "Contraloría", "escritura"),
    ("ALERTAS", "JEFE_DEPTO", "Tesorería", "lectura"),
]

# (acción, rol, departamento o None = cualquiera). Acciones sensibles por tipo de usuario.
PERMISOS_ACCION = [
    ("INHABILITAR_CIERRE", "ADMIN", None),
    ("INHABILITAR_CIERRE", "JEFE_DEPTO", "Contraloría"),
]

PARAMETROS = [
    ("TOLERANCIA_ABSOLUTA", "10.00", "Diferencia (en valor absoluto) aceptada sin generar alerta. El ruido normal del dataset llega a 4,81."),
    ("SEVERIDAD_MEDIA_PCT", "2.00", "Desde este % de diferencia sobre el monto sistema la alerta es de severidad media."),
    ("SEVERIDAD_ALTA_PCT", "10.00", "Desde este % de diferencia la alerta es de severidad alta."),
    ("SEVERIDAD_ALTA_MONTO", "500.00", "Desde este monto absoluto de diferencia la alerta es de severidad alta."),
    ("VENTANA_REINCIDENCIA_DIAS", "30", "Días hacia atrás que se miran para detectar reincidencia de un cajero."),
    ("MIN_ANOMALIAS_REINCIDENCIA", "3", "Cierres anómalos de un mismo cajero, dentro de la ventana, que disparan reincidencia."),
]


def correo_unico(nombres: str, apellidos: str, usados: set[str]) -> str:
    import unicodedata
    base = f"{nombres}.{apellidos}".lower().replace(" ", "")
    base = "".join(c for c in unicodedata.normalize("NFD", base) if unicodedata.category(c) != "Mn")
    correo, n = f"{base}@{DOMINIO}", 2
    while correo in usados:
        correo, n = f"{base}{n}@{DOMINIO}", n + 1
    usados.add(correo)
    return correo


def cargar_organizacion(db, password_hash: str) -> list[tuple[str, str, str]]:
    paises = {n: Pais(nombre=n, codigo_iso=c) for n, c in PAISES}
    niveles = {n: Nivel(nombre=n, orden=o) for n, o in NIVELES}
    deptos = {n: Departamento(nombre=n, descripcion=d) for n, d in DEPARTAMENTOS.items()}
    roles = {c: Rol(codigo=c, nombre=n) for c, n in [
        ("ADMIN", "Administrador"), ("JEFE_DEPTO", "Jefe de Departamento"), ("COLABORADOR", "Colaborador")]}
    db.add_all([*paises.values(), *niveles.values(), *deptos.values(), *roles.values()])

    funciones: dict[str, Funcion] = {}
    usados: set[str] = set()
    nombres_usados: set[tuple[str, str]] = set(PERSONAS_FIJAS.values()) | set(COLABORADORES_DEMO.values())
    cuentas_demo = []

    for depto_nombre, cargos in CARGOS.items():
        primer_analista_demo = True
        for (cargo_nombre, nivel, funcs), cantidad in zip(cargos, DOTACION[depto_nombre]):
            cargo = Cargo(nombre=cargo_nombre, departamento=deptos[depto_nombre], nivel=niveles[nivel])
            for f in funcs:
                funciones.setdefault(f, Funcion(descripcion=f))
                cargo.funciones.append(funciones[f])
            db.add(cargo)

            for i in range(cantidad):
                fijo = PERSONAS_FIJAS.get((depto_nombre, cargo_nombre))
                es_demo = (nivel == "Analista" and primer_analista_demo and depto_nombre in COLABORADORES_DEMO)
                if fijo:
                    nombres, apellidos = fijo
                elif es_demo:
                    nombres, apellidos = COLABORADORES_DEMO[depto_nombre]
                    primer_analista_demo = False
                else:
                    while True:
                        nombres, apellidos = rng.choice(NOMBRES), rng.choice(APELLIDOS)
                        if (nombres, apellidos) not in nombres_usados:
                            nombres_usados.add((nombres, apellidos))
                            break

                # El último Analista Junior de cada departamento queda inactivo
                inactivo = nivel == "Analista Junior" and i == cantidad - 1
                colab = Colaborador(
                    nombres=nombres, apellidos=apellidos,
                    correo=correo_unico(nombres, apellidos, usados),
                    pais=paises[rng.choices(["Venezuela", "Colombia", "Argentina"], [6, 2, 2])[0]],
                    fecha_ingreso=date(2014, 1, 1) + timedelta(days=rng.randint(0, 4300)),
                    estado="inactivo" if inactivo else "activo",
                    cargo=cargo,
                )
                if cargo_nombre.startswith("Administrador"):
                    rol = "ADMIN"
                elif nivel == "Gerente":
                    rol = "JEFE_DEPTO"
                else:
                    rol = "COLABORADOR"
                db.add(Usuario(colaborador=colab, rol=roles[rol], password_hash=password_hash,
                               activo=not inactivo))
                if fijo or es_demo:
                    cuentas_demo.append((rol, depto_nombre, colab.correo))

    modulos = {c: Modulo(codigo=c, nombre=n, descripcion=d, orden=o) for c, n, d, o in MODULOS}
    db.add_all(modulos.values())
    db.flush()  # asigna IDs a roles, departamentos y módulos
    for mod, rol, depto, nivel in PERMISOS:
        db.add(PermisoModulo(
            modulo_id=modulos[mod].id, rol_id=roles[rol].id,
            departamento_id=deptos[depto].id if depto else None, nivel_acceso=nivel,
        ))
    for accion, rol, depto in PERMISOS_ACCION:
        db.add(PermisoAccion(accion=accion, rol_id=roles[rol].id,
                             departamento_id=deptos[depto].id if depto else None))
    db.add_all(ParametroDeteccion(clave=k, valor=Decimal(v), descripcion=d) for k, v, d in PARAMETROS)
    db.flush()
    return cuentas_demo


def cargar_cierres(db) -> int:
    """Carga el dataset oficial de la prueba tal cual, leyéndolo con SQLite en memoria."""
    src = sqlite3.connect(":memory:")
    src.executescript(DATASET_CIERRES.read_text(encoding="utf-8"))
    paises = {p.nombre: p for p in db.query(Pais)}

    for id_, nombre, pais in src.execute("SELECT id, nombre, pais FROM tiendas ORDER BY id"):
        db.add(Tienda(id=id_, nombre=nombre, pais=paises[pais]))
    db.flush()
    for id_, nombre, tienda_id in src.execute("SELECT id, nombre, tienda_id FROM cajeros ORDER BY id"):
        db.add(Cajero(id=id_, nombre=nombre, tienda_id=tienda_id))
    db.flush()
    filas = src.execute(
        "SELECT id, tienda_id, cajero_id, fecha, CAST(monto_declarado AS TEXT), CAST(monto_sistema AS TEXT) "
        "FROM cierres_caja ORDER BY id").fetchall()
    for id_, tienda_id, cajero_id, fecha, declarado, sistema in filas:
        db.add(CierreCaja(
            id=id_, tienda_id=tienda_id, cajero_id=cajero_id, fecha=date.fromisoformat(fecha),
            # Se convierte desde texto para no pasar por float
            monto_declarado=Decimal(declarado).quantize(Decimal("0.01")),
            monto_sistema=Decimal(sistema).quantize(Decimal("0.01")),
            origen="carga_inicial",
        ))
    db.flush()
    return len(filas)


def ajustar_secuencias(db) -> None:
    """En PostgreSQL, al insertar IDs explícitos hay que mover la secuencia."""
    if engine.dialect.name != "postgresql":
        return
    from sqlalchemy import text
    for tabla in ("tienda", "cajero", "cierre_caja"):
        db.execute(text(f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), (SELECT MAX(id) FROM {tabla}))"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="Borra y recrea todas las tablas")
    parser.add_argument("--force-production", action="store_true")
    args = parser.parse_args()

    if settings.is_production and not args.force_production:
        sys.exit("APP_ENV=production: no se ejecuta la semilla sin --force-production.")
    pwd = settings.seed_demo_password
    if not pwd or len(pwd) < 10:
        sys.exit("Define SEED_DEMO_PASSWORD en .env (mínimo 10 caracteres).")

    if args.reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if db.query(Departamento).count():
            sys.exit("La base ya tiene datos. Usa --reset para recrearla.")
        cuentas = cargar_organizacion(db, hash_password(pwd))
        n_cierres = cargar_cierres(db)
        ajustar_secuencias(db)
        n_alertas = reprocesar_todo(db)
        db.commit()

        print(f"OK · {db.query(Colaborador).count()} colaboradores en {db.query(Departamento).count()} departamentos")
        print(f"OK · {n_cierres} cierres de caja cargados del dataset")
        print(f"OK · {n_alertas} alertas generadas por el motor de detección")
        print("\nCuentas de demostración (contraseña = SEED_DEMO_PASSWORD):")
        for rol, depto, correo in cuentas:
            print(f"  {rol:<12} {depto:<26} {correo}")


if __name__ == "__main__":
    main()
