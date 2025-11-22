from .geografia import router as geografia_router
from .temporal import router as temporal_router
from .victimas import router as victimas_router
from .clima import router as clima_router

__all__ = [
    "geografia_router",
    "temporal_router", 
    "victimas_router",
    "clima_router",
]
