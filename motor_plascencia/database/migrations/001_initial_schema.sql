-- ============================================================
-- motor_plascencia: esquema inicial de base de datos
-- Ejecutar UNA SOLA VEZ contra la base de datos atoms_db
-- ============================================================

-- 1. Tabla de Sistemas de Cancelaría (alimentada por la Maquinita Tragadata)
CREATE TABLE IF NOT EXISTS catalogo_sistemas (
    nombre_sistema VARCHAR(100) PRIMARY KEY,
    descuento_jamba_mm NUMERIC(6,2) NOT NULL,
    descuento_junquillo_mm NUMERIC(6,2) NOT NULL,
    descuento_vidrio_w_mm NUMERIC(6,2) NOT NULL,
    descuento_vidrio_h_mm NUMERIC(6,2) NOT NULL,
    momento_inercia_ix NUMERIC(6,3) DEFAULT 1.850,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Catálogo Maestro de Vidrios
CREATE TABLE IF NOT EXISTS vidrios_medidas (
    clave VARCHAR(50) PRIMARY KEY,
    tipo VARCHAR(100) NOT NULL,
    espesor_mm NUMERIC(4,1) NOT NULL
);

-- 3. Registro de Proyectos/Obras
CREATE TABLE IF NOT EXISTS proyectos (
    id_proyecto SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    fecha_creacion DATE DEFAULT CURRENT_DATE
);

-- 4. Lista de Materiales por Proyecto (BOM)
CREATE TABLE IF NOT EXISTS proyecto_materiales_detalles (
    id SERIAL PRIMARY KEY,
    id_proyecto INT REFERENCES proyectos(id_proyecto) ON DELETE CASCADE,
    tipo_material VARCHAR(50),      -- 'perfil', 'vidrio', 'herraje'
    clave_material VARCHAR(50),     -- Ej: '39073', 'VD-MONO-06'
    descripcion VARCHAR(200),
    cantidad NUMERIC(10,2),          -- Cantidad en metros o piezas
    unidad_medida VARCHAR(10)       -- 'mm', 'm', 'pza'
);

-- Datos de vidrios indispensables para que la app no falle
INSERT INTO vidrios_medidas (clave, tipo, espesor_mm) VALUES 
('VD-MONO-06', 'Monolitico Claro 6mm', 6.0),
('VD-TEMP-06', 'Templado de Seguridad 6mm', 6.0)
ON CONFLICT (clave) DO NOTHING;