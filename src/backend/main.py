"""
Observatorio de Ciudades — Apartadó, Antioquia
API Backend (FastAPI)
"""
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
from .routers import layers, geo, indicators, crossvar, stats

logger = logging.getLogger("observatorio")

TAGS_METADATA = [
    {"name": "Root", "description": "Health check y catálogo de endpoints"},
    {"name": "Capas", "description": "Catálogo de capas geoespaciales, GeoJSON y estadísticas"},
    {"name": "Geo", "description": "Datos geoespaciales filtrados: manzanas, edificaciones, vías, negocios, amenidades"},
    {"name": "Indicadores", "description": "Indicadores socioeconómicos, educativos, de seguridad, salud, economía y gobierno"},
    {"name": "Cruce de Variables", "description": "Análisis multivariado: scatter, correlación, series temporales"},
    {"name": "Estadísticas", "description": "Resumen ejecutivo y catálogo de datos"},
]

app = FastAPI(
    title="Observatorio de Ciudades — Apartadó",
    description=(
        "## API de datos territoriales\n\n"
        "Integra información geoespacial, socioeconómica, de seguridad, salud, "
        "educación, economía y gobernanza del municipio de **Apartadó, Antioquia** "
        "(DANE 05045), región de Urabá.\n\n"
        "### Fuentes de datos\n"
        "- **DANE**: Censo 2018, MGN, proyecciones poblacionales\n"
        "- **DNP**: TerriData (800+ indicadores municipales)\n"
        "- **ICFES**: Saber 11 resultados por colegio\n"
        "- **Policía Nacional**: Homicidios, hurtos, delitos sexuales, VIF\n"
        "- **Unidad de Víctimas**: Víctimas del conflicto armado\n"
        "- **INS**: SIVIGILA eventos epidemiológicos, IRCA calidad del agua\n"
        "- **MinTIC**: Internet fijo, índice de gobierno digital\n"
        "- **SECOP II**: Contratación pública\n"
        "- **MinCIT**: Registro Nacional de Turismo\n"
        "- **Google Places API**: Establecimientos comerciales\n"
        "- **OpenStreetMap**: Edificaciones, vías, amenidades\n\n"
        "### Base de datos\n"
        "**55 tablas** · **123,270 registros** · PostgreSQL + PostGIS 3.6\n\n"
        "### Frontend\n"
        "React 18 + Deck.gl + MapLibre GL + Recharts → `http://localhost:3000`"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=TAGS_METADATA,
)

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000",
).split(",")
# On Vercel the frontend and API share the same origin
VERCEL_URL = os.getenv("VERCEL_URL")
if VERCEL_URL:
    ALLOWED_ORIGINS.append(f"https://{VERCEL_URL}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(layers.router)
app.include_router(geo.router)
app.include_router(indicators.router)
app.include_router(crossvar.router)
app.include_router(stats.router)


@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": "Error de conexión a la base de datos"})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


@app.get("/", tags=["Root"])
def root():
    """Health check y catálogo de endpoints principales."""
    return {
        "name": "Observatorio de Ciudades — Apartadó",
        "version": "2.0.0",
        "municipio": "Apartadó",
        "departamento": "Antioquia",
        "dane_code": "05045",
        "database": {
            "tables": 55,
            "records": 123270,
            "schemas": ["cartografia", "socioeconomico", "seguridad", "servicios"],
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "layers": "/api/layers",
            "geo": "/api/geo/manzanas",
            "indicators": "/api/indicators",
            "crossvar": "/api/crossvar/variables",
            "stats": "/api/stats/summary",
            "catalog": "/api/stats/data-catalog",
            "terridata": "/api/indicators/terridata?dimension=Salud",
            "salud_irca": "/api/indicators/salud/irca",
            "salud_sivigila": "/api/indicators/salud/sivigila/resumen",
            "economia_internet": "/api/indicators/economia/internet/serie",
            "economia_secop": "/api/indicators/economia/secop",
            "economia_turismo": "/api/indicators/economia/turismo",
            "gobierno_finanzas": "/api/indicators/gobierno/finanzas",
            "gobierno_desempeno": "/api/indicators/gobierno/desempeno",
            "gobierno_digital": "/api/indicators/gobierno/digital",
            "gobierno_pobreza": "/api/indicators/gobierno/pobreza",
        },
    }
