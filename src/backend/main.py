"""
Observatorio de Ciudades — Urabá
API Backend (FastAPI)
"""
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
from .routers import layers, geo, indicators, crossvar, stats, empleo, analytics

logger = logging.getLogger("observatorio")

TAGS_METADATA = [
    {"name": "Root", "description": "Health check y catálogo de endpoints"},
    {"name": "Capas", "description": "Catálogo de capas geoespaciales, GeoJSON y estadísticas"},
    {"name": "Geo", "description": "Datos geoespaciales filtrados: manzanas, edificaciones, vías, negocios, amenidades"},
    {"name": "Indicadores", "description": "Indicadores socioeconómicos, educativos, de seguridad, salud, economía y gobierno"},
    {"name": "Cruce de Variables", "description": "Análisis multivariado: scatter, correlación, series temporales"},
    {"name": "Estadísticas", "description": "Resumen ejecutivo y catálogo de datos"},
    {"name": "Empleo", "description": "Mercado laboral y vacantes (Uraba Empleos)"},
    {"name": "Analytics", "description": "Inteligencia territorial, gaps y rankings regionales"},
]

app = FastAPI(
    title="Observatorio Laboral de Urabá",
    description=(
        "## API del Observatorio Laboral — Región de Urabá\n\n"
        "Plataforma de inteligencia territorial con enfoque en el **mercado laboral** "
        "que consolida información de empleo, economía, educación, salud y seguridad "
        "para los **11 municipios** de la subregión de Urabá, Antioquia.\n\n"
        "### Municipios Cubiertos\n"
        "- Apartadó, Turbo, Carepa, Chigorodó, Necoclí\n"
        "- Arboletes, San Juan de Urabá, San Pedro de Urabá\n"
        "- Mutatá, Murindó, Vigía del Fuerte\n\n"
        "### Fuentes de empleo\n"
        "- **Computrabajo, ElEmpleo, Indeed, LinkedIn**: Portales de empleo\n"
        "- **Comfama, Comfenalco**: Cajas de compensación\n"
        "- **SENA**: Agencia Pública de Empleo\n\n"
        "### Fuentes territoriales\n"
        "- **DANE**: Censo 2018, MGN, proyecciones\n"
        "- **DNP**: TerriData (Indicadores municipales comparados)\n"
        "- **ICFES**: Saber 11 resultados por colegio\n"
        "- **Policía Nacional**: Seguridad y convivencia\n"
        "- **Google Places**: Establecimientos comerciales\n\n"
        "### Frontend\n"
        "React 18 + Deck.gl + MapLibre GL + Recharts"
    ),
    version="4.0.0",
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
app.include_router(empleo.router)
app.include_router(analytics.router)


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
        "name": "Observatorio Laboral de Urabá",
        "version": "4.0.0",
        "municipios": [
            "Apartadó", "Turbo", "Carepa", "Chigorodó", "Necoclí",
            "Arboletes", "San Juan de Urabá", "San Pedro de Urabá",
            "Mutatá", "Murindó", "Vigía del Fuerte"
        ],
        "endpoints": {
            "docs": "/docs",
            "geo": "/api/geo/manzanas?dane_code=05045",
            "indicators": "/api/indicators",
            "empleo": "/api/empleo/ofertas",
            "analytics": "/api/analytics/ranking",
        },
    }
