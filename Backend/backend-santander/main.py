"""
Atlas al Crimen - Santander API
Backend para visualización de datos de seguridad y correlación climática
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import geografia_router, temporal_router, victimas_router, clima_router
from app.routers.filtros import router as filtros_router
from app.routers.chatbot import router as chatbot_router
from app.routers.predicciones import router as predicciones_router

# Crear tablas (solo si no existen)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    ## API para el Atlas al Crimen de Santander
    
    Esta API proporciona endpoints para:
    
    ### 📌 Sección 1 — Geografía
    - Mapa coroplético: delitos totales por municipio
    - Mapa coroplético: tasa por 100.000 habitantes
    
    ### 📌 Sección 2 — Temporal
    - Línea mensual de hurtos
    - Línea anual
    - Barras por día de semana y horas
    
    ### 📌 Sección 3 — Víctimas
    - Barras por género
    - Barras por grupo etario
    - Mapa de puntos con víctimas (lat/lon)
    
    ### 📌 Sección 4 — Clima
    - Scatter lluvia vs delitos
    - Barras lluvia por categorías
    - Línea de tiempo: lluvia y delitos superpuestos
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS - Permitir cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Debe ser False cuando allow_origins es ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Incluir routers
app.include_router(geografia_router, prefix=settings.API_PREFIX)
app.include_router(temporal_router, prefix=settings.API_PREFIX)
app.include_router(victimas_router, prefix=settings.API_PREFIX)
app.include_router(clima_router, prefix=settings.API_PREFIX)
app.include_router(filtros_router, prefix=settings.API_PREFIX)
app.include_router(chatbot_router, prefix=settings.API_PREFIX)
app.include_router(predicciones_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "nombre": "Atlas al Crimen - Santander API",
        "version": settings.API_VERSION,
        "documentacion": "/docs",
        "endpoints": {
            "geografia": f"{settings.API_PREFIX}/geografia",
            "temporal": f"{settings.API_PREFIX}/temporal",
            "victimas": f"{settings.API_PREFIX}/victimas",
            "clima": f"{settings.API_PREFIX}/clima",
            "filtros": f"{settings.API_PREFIX}/filtros",
            "chatbot": f"{settings.API_PREFIX}/chatbot",
            "predicciones": f"{settings.API_PREFIX}/predicciones",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
