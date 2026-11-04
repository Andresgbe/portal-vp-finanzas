-- Generado desde backend/app/models.py con scripts/export_schema.py
-- Motor: PostgreSQL. Los datos semilla se cargan con scripts/seed.py

CREATE TABLE departamento (
	id SERIAL NOT NULL, 
	nombre VARCHAR(80) NOT NULL, 
	descripcion VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE funcion (
	id SERIAL NOT NULL, 
	descripcion VARCHAR(200) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (descripcion)
);

CREATE TABLE modulo (
	id SERIAL NOT NULL, 
	codigo VARCHAR(30) NOT NULL, 
	nombre VARCHAR(80) NOT NULL, 
	descripcion VARCHAR(255) NOT NULL, 
	orden INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);

CREATE TABLE nivel (
	id SERIAL NOT NULL, 
	nombre VARCHAR(40) NOT NULL, 
	orden INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre), 
	UNIQUE (orden)
);

CREATE TABLE pais (
	id SERIAL NOT NULL, 
	nombre VARCHAR(60) NOT NULL, 
	codigo_iso VARCHAR(2) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre), 
	UNIQUE (codigo_iso)
);

CREATE TABLE parametro_deteccion (
	clave VARCHAR(40) NOT NULL, 
	valor NUMERIC(12, 2) NOT NULL, 
	descripcion VARCHAR(255) NOT NULL, 
	PRIMARY KEY (clave)
);

CREATE TABLE rol (
	id SERIAL NOT NULL, 
	codigo VARCHAR(20) NOT NULL, 
	nombre VARCHAR(60) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);

CREATE TABLE cargo (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	departamento_id INTEGER NOT NULL, 
	nivel_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre, departamento_id), 
	FOREIGN KEY(departamento_id) REFERENCES departamento (id), 
	FOREIGN KEY(nivel_id) REFERENCES nivel (id)
);

CREATE TABLE permiso_modulo (
	id SERIAL NOT NULL, 
	modulo_id INTEGER NOT NULL, 
	rol_id INTEGER NOT NULL, 
	departamento_id INTEGER, 
	nivel_acceso VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (modulo_id, rol_id, departamento_id), 
	CONSTRAINT ck_permiso_nivel CHECK (nivel_acceso IN ('lectura','escritura')), 
	FOREIGN KEY(modulo_id) REFERENCES modulo (id), 
	FOREIGN KEY(rol_id) REFERENCES rol (id), 
	FOREIGN KEY(departamento_id) REFERENCES departamento (id)
);

CREATE TABLE tienda (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	pais_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre), 
	FOREIGN KEY(pais_id) REFERENCES pais (id)
);

CREATE TABLE cajero (
	id SERIAL NOT NULL, 
	nombre VARCHAR(150) NOT NULL, 
	tienda_id INTEGER NOT NULL, 
	activo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tienda_id) REFERENCES tienda (id)
);

CREATE TABLE cargo_funcion (
	cargo_id INTEGER NOT NULL, 
	funcion_id INTEGER NOT NULL, 
	PRIMARY KEY (cargo_id, funcion_id), 
	FOREIGN KEY(cargo_id) REFERENCES cargo (id) ON DELETE CASCADE, 
	FOREIGN KEY(funcion_id) REFERENCES funcion (id) ON DELETE RESTRICT
);

CREATE TABLE colaborador (
	id SERIAL NOT NULL, 
	nombres VARCHAR(80) NOT NULL, 
	apellidos VARCHAR(80) NOT NULL, 
	correo VARCHAR(120) NOT NULL, 
	pais_id INTEGER NOT NULL, 
	fecha_ingreso DATE NOT NULL, 
	estado VARCHAR(10) NOT NULL, 
	cargo_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_colaborador_estado CHECK (estado IN ('activo','inactivo')), 
	UNIQUE (correo), 
	FOREIGN KEY(pais_id) REFERENCES pais (id), 
	FOREIGN KEY(cargo_id) REFERENCES cargo (id)
);

CREATE TABLE usuario (
	id SERIAL NOT NULL, 
	colaborador_id INTEGER NOT NULL, 
	rol_id INTEGER NOT NULL, 
	password_hash VARCHAR(100) NOT NULL, 
	activo BOOLEAN NOT NULL, 
	intentos_fallidos INTEGER NOT NULL, 
	bloqueado_hasta TIMESTAMP WITH TIME ZONE, 
	ultimo_acceso TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (colaborador_id), 
	FOREIGN KEY(colaborador_id) REFERENCES colaborador (id), 
	FOREIGN KEY(rol_id) REFERENCES rol (id)
);

CREATE TABLE cierre_caja (
	id SERIAL NOT NULL, 
	tienda_id INTEGER NOT NULL, 
	cajero_id INTEGER NOT NULL, 
	fecha DATE NOT NULL, 
	monto_declarado NUMERIC(12, 2) NOT NULL, 
	monto_sistema NUMERIC(12, 2) NOT NULL, 
	origen VARCHAR(15) NOT NULL, 
	registrado_por_id INTEGER, 
	registrado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_cierre_declarado CHECK (monto_declarado >= 0), 
	CONSTRAINT ck_cierre_sistema CHECK (monto_sistema >= 0), 
	CONSTRAINT ck_cierre_origen CHECK (origen IN ('carga_inicial','portal')), 
	FOREIGN KEY(tienda_id) REFERENCES tienda (id), 
	FOREIGN KEY(cajero_id) REFERENCES cajero (id), 
	FOREIGN KEY(registrado_por_id) REFERENCES usuario (id)
);

CREATE INDEX ix_cierre_caja_cajero_id ON cierre_caja (cajero_id);

CREATE INDEX ix_cierre_caja_fecha ON cierre_caja (fecha);

CREATE TABLE alerta (
	id SERIAL NOT NULL, 
	cierre_id INTEGER NOT NULL, 
	regla VARCHAR(20) NOT NULL, 
	severidad VARCHAR(5) NOT NULL, 
	detalle TEXT NOT NULL, 
	estado VARCHAR(10) NOT NULL, 
	creada_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_alerta_cierre_regla UNIQUE (cierre_id, regla), 
	CONSTRAINT ck_alerta_regla CHECK (regla IN ('FUERA_DE_RANGO', 'TRANSPOSICION', 'REINCIDENCIA', 'DUPLICADO')), 
	CONSTRAINT ck_alerta_severidad CHECK (severidad IN ('baja', 'media', 'alta')), 
	CONSTRAINT ck_alerta_estado CHECK (estado IN ('pendiente', 'revisada', 'descartada')), 
	FOREIGN KEY(cierre_id) REFERENCES cierre_caja (id)
);

CREATE INDEX ix_alerta_cierre_id ON alerta (cierre_id);

CREATE INDEX ix_alerta_estado ON alerta (estado);

CREATE TABLE alerta_historial (
	id SERIAL NOT NULL, 
	alerta_id INTEGER NOT NULL, 
	estado_anterior VARCHAR(10), 
	estado_nuevo VARCHAR(10) NOT NULL, 
	usuario_id INTEGER, 
	fecha TIMESTAMP WITH TIME ZONE NOT NULL, 
	comentario VARCHAR(500) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(alerta_id) REFERENCES alerta (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuario (id)
);

CREATE INDEX ix_alerta_historial_alerta_id ON alerta_historial (alerta_id);
