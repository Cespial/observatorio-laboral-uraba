-- ============================================================
-- OBSERVATORIO DE CIUDADES — URABÁ
-- Schema de Base de Datos PostGIS
-- ============================================================

-- Esquemas temáticos
CREATE SCHEMA IF NOT EXISTS cartografia;
CREATE SCHEMA IF NOT EXISTS socioeconomico;
CREATE SCHEMA IF NOT EXISTS seguridad;
CREATE SCHEMA IF NOT EXISTS servicios;
CREATE SCHEMA IF NOT EXISTS catastro;
CREATE SCHEMA IF NOT EXISTS ambiental;

-- ============================================================
-- CARTOGRAFÍA BASE
-- ============================================================

CREATE TABLE IF NOT EXISTS cartografia.limite_municipal (
    dane_code VARCHAR(5),
    nombre VARCHAR(100),
    divipola VARCHAR(10),
    departamento VARCHAR(100),
    area_km2 NUMERIC,
    geom GEOMETRY(Polygon, 4326),
    PRIMARY KEY (dane_code)
);
CREATE INDEX IF NOT EXISTS idx_limite_municipal_dane ON cartografia.limite_municipal(dane_code);

CREATE TABLE IF NOT EXISTS cartografia.osm_edificaciones (
    id BIGINT,
    dane_code VARCHAR(5),
    osm_type VARCHAR(20),
    building VARCHAR(100),
    name VARCHAR(255),
    amenity VARCHAR(100),
    addr_street VARCHAR(255),
    geom GEOMETRY(Polygon, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_osm_edificaciones_dane ON cartografia.osm_edificaciones(dane_code);

CREATE TABLE IF NOT EXISTS cartografia.osm_vias (
    id BIGINT,
    dane_code VARCHAR(5),
    osm_type VARCHAR(20),
    highway VARCHAR(100),
    name VARCHAR(255),
    surface VARCHAR(100),
    lanes INTEGER,
    geom GEOMETRY(LineString, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_osm_vias_dane ON cartografia.osm_vias(dane_code);

CREATE TABLE IF NOT EXISTS cartografia.osm_uso_suelo (
    id BIGINT,
    dane_code VARCHAR(5),
    landuse VARCHAR(100),
    name VARCHAR(255),
    geom GEOMETRY(Polygon, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_osm_uso_suelo_dane ON cartografia.osm_uso_suelo(dane_code);

CREATE TABLE IF NOT EXISTS cartografia.osm_amenidades (
    id BIGINT,
    dane_code VARCHAR(5),
    amenity VARCHAR(100),
    name VARCHAR(255),
    phone VARCHAR(100),
    website VARCHAR(500),
    opening_hours VARCHAR(255),
    lat NUMERIC,
    lon NUMERIC,
    geom GEOMETRY(Point, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_osm_amenidades_dane ON cartografia.osm_amenidades(dane_code);

-- ============================================================
-- MGN — MANZANAS CENSALES
-- ============================================================

CREATE TABLE IF NOT EXISTS cartografia.manzanas_censales (
    id SERIAL,
    dane_code VARCHAR(5),
    cod_dane_manzana VARCHAR(30),
    cod_dane_seccion VARCHAR(20),
    cod_dane_sector VARCHAR(20),
    cod_dane_municipio VARCHAR(10),
    tipo VARCHAR(50),
    total_personas INTEGER,
    total_hogares INTEGER,
    total_viviendas INTEGER,
    viviendas_ocupadas INTEGER,
    personas_hombres INTEGER,
    personas_mujeres INTEGER,
    geom GEOMETRY(MultiPolygon, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_manzanas_dane ON cartografia.manzanas_censales(dane_code);
CREATE INDEX IF NOT EXISTS idx_manzanas_municipio ON cartografia.manzanas_censales(cod_dane_municipio);
CREATE INDEX IF NOT EXISTS idx_manzanas_geom ON cartografia.manzanas_censales USING GIST(geom);

-- ============================================================
-- CATASTRO
-- ============================================================

CREATE TABLE IF NOT EXISTS catastro.terrenos (
    id SERIAL,
    dane_code VARCHAR(5),
    codigo_predial VARCHAR(50),
    municipio VARCHAR(100),
    cod_municipio VARCHAR(10),
    area_terreno NUMERIC,
    avaluo_catastral NUMERIC,
    destino_economico VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_terrenos_dane ON catastro.terrenos(dane_code);
CREATE INDEX IF NOT EXISTS idx_terrenos_municipio ON catastro.terrenos(cod_municipio);
CREATE INDEX IF NOT EXISTS idx_terrenos_geom ON catastro.terrenos USING GIST(geom);

CREATE TABLE IF NOT EXISTS catastro.construcciones (
    id SERIAL,
    dane_code VARCHAR(5),
    codigo_predial VARCHAR(50),
    municipio VARCHAR(100),
    cod_municipio VARCHAR(10),
    area_construida NUMERIC,
    tipo_construccion VARCHAR(100),
    pisos INTEGER,
    geom GEOMETRY(MultiPolygon, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_construcciones_dane ON catastro.construcciones(dane_code);

CREATE TABLE IF NOT EXISTS catastro.sectores (
    id SERIAL,
    dane_code VARCHAR(5),
    codigo VARCHAR(50),
    nombre VARCHAR(255),
    municipio VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_sectores_dane ON catastro.sectores(dane_code);

CREATE TABLE IF NOT EXISTS catastro.veredas (
    id SERIAL,
    dane_code VARCHAR(5),
    codigo VARCHAR(50),
    nombre VARCHAR(255),
    municipio VARCHAR(100),
    area_ha NUMERIC,
    geom GEOMETRY(MultiPolygon, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_veredas_dane ON catastro.veredas(dane_code);

-- ============================================================
-- SOCIOECONÓMICO
-- ============================================================

CREATE TABLE IF NOT EXISTS socioeconomico.ipm (
    id SERIAL,
    dane_code VARCHAR(5),
    cod_municipio VARCHAR(10),
    municipio VARCHAR(100),
    departamento VARCHAR(100),
    ipm_total NUMERIC,
    bajo_logro_educativo NUMERIC,
    analfabetismo NUMERIC,
    inasistencia_escolar NUMERIC,
    rezago_escolar NUMERIC,
    barreras_salud NUMERIC,
    sin_aseguramiento NUMERIC,
    sin_agua NUMERIC,
    sin_alcantarillado NUMERIC,
    pisos_inadecuados NUMERIC,
    paredes_inadecuadas NUMERIC,
    hacinamiento NUMERIC,
    trabajo_infantil NUMERIC,
    alta_dependencia NUMERIC,
    empleo_informal NUMERIC,
    sin_internet NUMERIC,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_ipm_dane ON socioeconomico.ipm(dane_code);

CREATE TABLE IF NOT EXISTS socioeconomico.nbi (
    id SERIAL,
    dane_code VARCHAR(5),
    cod_municipio VARCHAR(10),
    municipio VARCHAR(100),
    departamento VARCHAR(100),
    nbi_total NUMERIC,
    nbi_urbano NUMERIC,
    nbi_rural NUMERIC,
    prop_miseria NUMERIC,
    comp_vivienda NUMERIC,
    comp_servicios NUMERIC,
    comp_hacinamiento NUMERIC,
    comp_inasistencia NUMERIC,
    comp_dependencia NUMERIC,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_nbi_dane ON socioeconomico.nbi(dane_code);

CREATE TABLE IF NOT EXISTS socioeconomico.establecimientos_educativos (
    id SERIAL,
    dane_code VARCHAR(5),
    codigo_dane VARCHAR(20),
    nombre VARCHAR(255),
    municipio VARCHAR(100),
    cod_municipio VARCHAR(10),
    sector VARCHAR(50),
    calendario VARCHAR(20),
    direccion VARCHAR(255),
    telefono VARCHAR(50),
    total_matricula INTEGER,
    cantidad_sedes INTEGER,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_establecimientos_dane ON socioeconomico.establecimientos_educativos(dane_code);

CREATE TABLE IF NOT EXISTS socioeconomico.icfes (
    id SERIAL,
    dane_code VARCHAR(5),
    periodo VARCHAR(20),
    cole_nombre VARCHAR(255),
    cole_cod_dane VARCHAR(20),
    cole_mcpio VARCHAR(100),
    punt_lectura_critica NUMERIC,
    punt_matematicas NUMERIC,
    punt_c_naturales NUMERIC,
    punt_sociales NUMERIC,
    punt_ingles NUMERIC,
    punt_global NUMERIC,
    estu_genero VARCHAR(10),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_icfes_dane ON socioeconomico.icfes(dane_code);

CREATE TABLE IF NOT EXISTS socioeconomico.ips_salud (
    id SERIAL,
    dane_code VARCHAR(5),
    codigo_habilitacion VARCHAR(30),
    nombre VARCHAR(255),
    municipio VARCHAR(100),
    cod_municipio VARCHAR(10),
    departamento VARCHAR(100),
    clase_persona VARCHAR(50),
    nivel_atencion VARCHAR(20),
    caracter VARCHAR(50),
    direccion VARCHAR(255),
    telefono VARCHAR(50),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_ips_salud_dane ON socioeconomico.ips_salud(dane_code);

CREATE TABLE IF NOT EXISTS socioeconomico.prestadores_servicios (
    id SERIAL,
    dane_code VARCHAR(5),
    nit VARCHAR(20),
    razon_social VARCHAR(255),
    municipio VARCHAR(100),
    cod_municipio VARCHAR(10),
    servicio VARCHAR(255),
    cobertura NUMERIC,
    suscriptores INTEGER,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_prestadores_dane ON socioeconomico.prestadores_servicios(dane_code);

-- ============================================================
-- SEGURIDAD Y CONFLICTO
-- ============================================================

CREATE TABLE IF NOT EXISTS seguridad.homicidios (
    id SERIAL,
    dane_code VARCHAR(5),
    fecha DATE,
    municipio VARCHAR(100),
    cod_municipio VARCHAR(20),
    departamento VARCHAR(100),
    genero VARCHAR(20),
    grupo_etario VARCHAR(50),
    arma_medio VARCHAR(100),
    cantidad INTEGER,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_homicidios_dane ON seguridad.homicidios(dane_code);

CREATE TABLE IF NOT EXISTS seguridad.hurtos (
    id SERIAL,
    dane_code VARCHAR(5),
    fecha DATE,
    municipio VARCHAR(100),
    cod_municipio VARCHAR(20),
    departamento VARCHAR(100),
    tipo_hurto VARCHAR(100),
    genero VARCHAR(20),
    grupo_etario VARCHAR(50),
    arma_medio VARCHAR(100),
    cantidad INTEGER,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_hurtos_dane ON seguridad.hurtos(dane_code);

CREATE TABLE IF NOT EXISTS seguridad.delitos_sexuales (
    id SERIAL,
    dane_code VARCHAR(5),
    fecha DATE,
    municipio VARCHAR(100),
    cod_municipio VARCHAR(20),
    departamento VARCHAR(100),
    genero VARCHAR(20),
    grupo_etario VARCHAR(50),
    cantidad INTEGER,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_delitos_sexuales_dane ON seguridad.delitos_sexuales(dane_code);

CREATE TABLE IF NOT EXISTS seguridad.violencia_intrafamiliar (
    id SERIAL,
    dane_code VARCHAR(5),
    fecha DATE,
    municipio VARCHAR(100),
    cod_municipio VARCHAR(20),
    departamento VARCHAR(100),
    genero VARCHAR(20),
    grupo_etario VARCHAR(50),
    arma_medio VARCHAR(100),
    cantidad INTEGER,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_violencia_intra_dane ON seguridad.violencia_intrafamiliar(dane_code);

CREATE TABLE IF NOT EXISTS seguridad.victimas_conflicto (
    id SERIAL,
    dane_code VARCHAR(5),
    cod_municipio VARCHAR(10),
    municipio VARCHAR(100),
    departamento VARCHAR(100),
    hecho VARCHAR(100),
    sexo VARCHAR(20),
    etnia VARCHAR(100),
    ciclo_vital VARCHAR(50),
    discapacidad VARCHAR(10),
    personas INTEGER,
    eventos INTEGER,
    fecha_corte DATE,
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_victimas_dane ON seguridad.victimas_conflicto(dane_code);

-- ============================================================
-- GOOGLE PLACES
-- ============================================================

CREATE TABLE IF NOT EXISTS servicios.google_places (
    id SERIAL,
    dane_code VARCHAR(5),
    place_id VARCHAR(255),
    name VARCHAR(500),
    category VARCHAR(100),
    types TEXT[],
    address VARCHAR(500),
    rating NUMERIC,
    user_ratings_total INTEGER,
    price_level INTEGER,
    phone VARCHAR(50),
    website VARCHAR(500),
    lat NUMERIC,
    lon NUMERIC,
    geom GEOMETRY(Point, 4326),
    PRIMARY KEY (id, dane_code)
);
CREATE INDEX IF NOT EXISTS idx_places_dane ON servicios.google_places(dane_code);
CREATE INDEX IF NOT EXISTS idx_places_geom ON servicios.google_places USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_places_category ON servicios.google_places(category);

-- ============================================================
-- VISTAS MATERIALIZADAS para cruces rápidos
-- ============================================================

-- Se crearán después de cargar datos

-- ============================================================
-- EMPLEO — Columnas de enriquecimiento NLP
-- ============================================================
CREATE SCHEMA IF NOT EXISTS empleo;

CREATE TABLE IF NOT EXISTS empleo.ofertas_laborales (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    empresa TEXT,
    salario_texto TEXT,
    salario_numerico INTEGER,
    descripcion TEXT,
    fecha_publicacion DATE,
    enlace TEXT,
    municipio TEXT NOT NULL,
    dane_code TEXT,
    fuente TEXT NOT NULL,
    sector TEXT,
    skills TEXT[],
    fecha_scraping TIMESTAMP,
    content_hash TEXT,
    dedup_hash TEXT,
    nivel_experiencia TEXT,
    tipo_contrato TEXT,
    nivel_educativo TEXT,
    modalidad TEXT
);

ALTER TABLE empleo.ofertas_laborales ADD COLUMN IF NOT EXISTS nivel_experiencia TEXT;
ALTER TABLE empleo.ofertas_laborales ADD COLUMN IF NOT EXISTS tipo_contrato TEXT;
ALTER TABLE empleo.ofertas_laborales ADD COLUMN IF NOT EXISTS nivel_educativo TEXT;
ALTER TABLE empleo.ofertas_laborales ADD COLUMN IF NOT EXISTS modalidad TEXT;
ALTER TABLE empleo.ofertas_laborales ADD COLUMN IF NOT EXISTS dedup_hash TEXT;

-- Deduplication index: prevents same job from appearing twice across portals
CREATE UNIQUE INDEX IF NOT EXISTS idx_ofertas_dedup_hash
ON empleo.ofertas_laborales (dedup_hash)
WHERE dedup_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ofertas_content_hash
ON empleo.ofertas_laborales (content_hash)
WHERE content_hash IS NOT NULL;
