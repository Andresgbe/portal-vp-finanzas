-- =====================================================================
-- DATA DE EJEMPLO — Caso 1: Detector de anomalías en cierres de caja
-- Farmatodo · Transformación Financiera · Prueba Técnica
-- TODOS los datos son ficticios (tiendas, cajeros y montos no representan
-- información real).
--
-- CÓMO USAR ESTE ARCHIVO:
-- Este es un dataset de ejemplo que puedes usar como semilla para tu base
-- de datos, si quieres ahorrarte el paso de inventar los datos desde cero.
-- Es opcional: puedes usarlo tal cual, modificarlo, o generar el tuyo propio
-- con AI o scripts — lo que se evalúa es el modelo relacional y la lógica
-- que construyas encima, no el origen de los datos.
--
-- Contiene `cierres_caja`: el monto que el cajero declaró al cerrar caja
-- (`monto_declarado`) frente al monto que el sistema registró para ese turno
-- (`monto_sistema`). Algunos registros tienen diferencias entre ambos montos
-- — sobre eso debes construir tu propia lógica de detección de anomalías,
-- según lo descrito en la Opción 1 de la sección 3.4 del enunciado.
-- =====================================================================

-- Esquema de referencia (ajusta tipos según tu motor de BD elegido)

CREATE TABLE tiendas (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    unidad_organizativa VARCHAR(50) NOT NULL DEFAULT 'Operación'
);

CREATE TABLE cajeros (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    cargo VARCHAR(50) NOT NULL DEFAULT 'Cajero de Tienda',
    unidad_organizativa VARCHAR(50) NOT NULL DEFAULT 'Operación',
    tienda_id INTEGER NOT NULL REFERENCES tiendas(id)
);

CREATE TABLE cierres_caja (
    id INTEGER PRIMARY KEY,
    tienda_id INTEGER NOT NULL REFERENCES tiendas(id),
    cajero_id INTEGER NOT NULL REFERENCES cajeros(id),
    fecha DATE NOT NULL,
    monto_declarado DECIMAL(12,2) NOT NULL,
    monto_sistema DECIMAL(12,2) NOT NULL
);

-- ---------------------------------------------------------------------
-- TIENDAS (unidad_organizativa = 'Operación')
-- ---------------------------------------------------------------------
INSERT INTO tiendas (id, nombre, pais, unidad_organizativa) VALUES (1, 'Tienda Chacao', 'Venezuela', 'Operación');
INSERT INTO tiendas (id, nombre, pais, unidad_organizativa) VALUES (2, 'Tienda Las Mercedes', 'Venezuela', 'Operación');
INSERT INTO tiendas (id, nombre, pais, unidad_organizativa) VALUES (3, 'Tienda Maracaibo Centro', 'Venezuela', 'Operación');
INSERT INTO tiendas (id, nombre, pais, unidad_organizativa) VALUES (4, 'Tienda Palermo', 'Argentina', 'Operación');
INSERT INTO tiendas (id, nombre, pais, unidad_organizativa) VALUES (5, 'Tienda Belgrano', 'Argentina', 'Operación');
INSERT INTO tiendas (id, nombre, pais, unidad_organizativa) VALUES (6, 'Tienda Córdoba Norte', 'Argentina', 'Operación');

-- ---------------------------------------------------------------------
-- CAJEROS (unidad_organizativa = 'Operación')
-- ---------------------------------------------------------------------
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (1, 'Rosa Delgado', 'Cajero de Tienda', 'Operación', 3);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (2, 'Miguel Ochoa', 'Cajero de Tienda', 'Operación', 2);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (3, 'Yelitza Bravo', 'Cajero de Tienda', 'Operación', 4);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (4, 'Franklin Uzcátegui', 'Cajero de Tienda', 'Operación', 6);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (5, 'Carla Beltrán', 'Cajero de Tienda', 'Operación', 1);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (6, 'Hugo Sandoval', 'Cajero de Tienda', 'Operación', 1);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (7, 'Ana Bracho', 'Cajero de Tienda', 'Operación', 5);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (8, 'Wilmer Colmenares', 'Cajero de Tienda', 'Operación', 1);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (9, 'Estefanía Requena', 'Cajero de Tienda', 'Operación', 3);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (10, 'Bruno Villalba', 'Cajero de Tienda', 'Operación', 5);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (11, 'Marcos Ledesma', 'Cajero de Tienda', 'Operación', 1);
INSERT INTO cajeros (id, nombre, cargo, unidad_organizativa, tienda_id) VALUES (12, 'Rocío Funes', 'Cajero de Tienda', 'Operación', 5);

-- ---------------------------------------------------------------------
-- CIERRES DE CAJA (60 registros: la mayoría normales, algunos con
-- diferencias entre monto declarado y monto de sistema)
-- ---------------------------------------------------------------------
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (1, 6, 4, '2026-06-03', 959.2, 961.79);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (2, 3, 9, '2026-06-28', 759.62, 755.15);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (3, 1, 11, '2026-07-11', 4789.94, 4789.08);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (4, 3, 1, '2026-06-15', 1152.09, 658.69);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (5, 3, 9, '2026-06-08', 4697.86, 4696.04);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (6, 2, 2, '2026-07-08', 4694.24, 4698.27);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (7, 5, 12, '2026-06-05', 4645.6, 4645.64);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (8, 3, 9, '2026-06-28', 6288.89, 6284.66);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (9, 1, 6, '2026-06-20', 2215.68, 2212.88);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (10, 2, 2, '2026-07-07', 2610.35, 2611.92);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (11, 1, 8, '2026-06-19', 4989.1, 4988.98);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (12, 4, 3, '2026-06-22', 1465.67, 1470.28);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (13, 1, 11, '2026-06-05', 6190.95, 6187.2);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (14, 1, 6, '2026-06-22', 5654.57, 5653.77);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (15, 1, 8, '2026-06-05', 6947.75, 6767.75);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (16, 5, 12, '2026-07-13', 800.5, 800.5);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (17, 1, 11, '2026-07-07', 8648.48, 7946.84);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (18, 1, 11, '2026-06-23', 470.41, 473.73);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (19, 2, 2, '2026-07-02', 573.95, 753.95);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (20, 5, 12, '2026-06-16', 3620.22, 3363.81);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (21, 1, 8, '2026-06-26', 5335.48, 4530.69);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (22, 1, 5, '2026-07-16', 3501.62, 3497.78);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (23, 6, 4, '2026-06-10', 940.57, 938.98);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (24, 3, 1, '2026-07-02', 6697.24, 6699.42);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (25, 4, 3, '2026-06-27', 4414.54, 4416.35);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (26, 4, 3, '2026-07-15', 6765.86, 6915.86);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (27, 1, 8, '2026-07-14', 6442.61, 6443.62);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (28, 2, 2, '2026-07-01', 5179.7, 5184.03);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (29, 6, 4, '2026-06-29', 1545.26, 1549.73);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (30, 3, 1, '2026-07-07', 1463.38, 1464.74);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (31, 3, 1, '2026-06-05', 7028.85, 7032.36);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (32, 1, 5, '2026-06-23', 4933.7, 4937.55);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (33, 1, 8, '2026-06-30', 3995.48, 3999.04);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (34, 5, 12, '2026-06-22', 6002.62, 6000.7);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (35, 3, 9, '2026-06-02', 1700.16, 1880.16);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (36, 4, 3, '2026-07-15', 4482.71, 4482.43);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (37, 1, 11, '2026-06-06', 5659.39, 5660.72);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (38, 4, 3, '2026-06-23', 6246.71, 6243.92);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (39, 1, 6, '2026-07-11', 1253.16, 2017.42);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (40, 5, 7, '2026-06-15', 1841.68, 1839.37);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (41, 3, 1, '2026-06-18', 3937.3, 3936.25);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (42, 1, 6, '2026-06-29', 6255.96, 6525.96);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (43, 1, 6, '2026-06-06', 1994.53, 1997.56);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (44, 6, 4, '2026-07-01', 4569.68, 5105.31);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (45, 1, 11, '2026-06-23', 6458.87, 6457.26);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (46, 5, 7, '2026-07-16', 6072.87, 6076.08);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (47, 1, 11, '2026-06-22', 1147.97, 967.97);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (48, 1, 8, '2026-06-26', 6020.41, 6023.82);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (49, 4, 3, '2026-06-02', 835.76, 1463.86);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (50, 5, 10, '2026-07-01', 5361.46, 5360.97);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (51, 4, 3, '2026-06-02', 259.67, 409.67);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (52, 3, 9, '2026-06-09', 3420.73, 3640.33);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (53, 6, 4, '2026-06-19', 4518.95, 4158.95);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (54, 1, 5, '2026-07-05', 3530.5, 3526.4);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (55, 1, 6, '2026-06-30', 6180.06, 5401.06);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (56, 3, 9, '2026-06-09', 4390.24, 4395.05);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (57, 1, 8, '2026-06-12', 9485.87, 4985.87);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (58, 4, 3, '2026-06-10', 3954.9, 3945.9);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (59, 3, 1, '2026-06-21', 5553.77, 5553.95);
INSERT INTO cierres_caja (id, tienda_id, cajero_id, fecha, monto_declarado, monto_sistema) VALUES (60, 2, 2, '2026-07-06', 732.95, 737.53);