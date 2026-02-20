# Observatorio Regional Urabá — Guía de Desarrollo

Este proyecto ha evolucionado de un observatorio local (Apartadó) a una plataforma de inteligencia territorial regional que cubre los 11 municipios de la subregión de Urabá, Antioquia.

## 🏗 Arquitectura de Datos Regional

### 1. Municipios Soportados
- **Eje Bananero:** Apartadó (05045), Carepa (05147), Chigorodó (05172), Turbo (05837).
- **Urabá Norte:** Necoclí (05490), San Pedro de Urabá (05665), San Juan de Urabá (05659), Arboletes (05051).
- **Atrato / Sur:** Mutatá (05480), Murindó (05475), Vigía del Fuerte (05873).

### 2. Estructura de Base de Datos (Supabase/PostGIS)
Todas las tablas geográficas y estadísticas ahora incluyen la columna `dane_code` para permitir el filtrado y la agregación regional.

- **`cartografia.veredas_mgn`**: Contiene los polígonos de las 610 secciones rurales de la región (MGN 2019).
- **`servicios.google_places_regional`**: Repositorio dinámico de servicios y comercio poblado mediante webscraping masivo.
- **`socioeconomico.terridata`**: Indicadores oficiales del DNP para toda la subregión.

## 🚀 Cómo añadir un nuevo indicador regional

1.  **ETL:** Colocar el archivo fuente en `data/<categoria>/`. Asegurarse de que el script en `etl/` procese todos los códigos DANE de Urabá.
2.  **Backend:** Actualizar el router correspondiente en `src/backend/routers/` para que acepte `?dane_code=`.
3.  **Frontend:** El `store.js` ya maneja el estado global del municipio seleccionado. Cualquier componente nuevo que use `fetch` debe inyectar el código DANE desde el store.

## 🛠 Comandos de Ingesta Masiva

Para repoblar la base de datos regional:
```bash
# Instalar dependencias pesadas
pip install -r requirements-etl.txt

# Ingesta cartográfica rural
python etl/06_ingest_mgn.py

# Scraping masivo de servicios (Google Places)
python etl/07_scrape_places_regional.py
```

## 📋 Estándares de Código
- **Backend:** FastAPI, tipado estricto, documentación OpenAPI en `/docs`.
- **Frontend:** React 18, Zustand para estado, Deck.gl para mapas de alto rendimiento.
