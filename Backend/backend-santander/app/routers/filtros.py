"""
Seccion de Filtros - Opciones disponibles para selectores
Proporciona listas de valores unicos para poblar dropdowns en el frontend
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from ..database import get_db
from ..models import FactSeguridad, MasterMunicipios

router = APIRouter(prefix="/filtros", tags=["Filtros y Opciones"])


@router.get("/municipios")
async def get_municipios(db: Session = Depends(get_db)):
    """
    Lista todos los municipios de Santander para selectores.
    Retorna codigo_dane, nombre y categoria (rural/urbana).
    """
    results = db.query(
        MasterMunicipios.codigo_dane,
        MasterMunicipios.nombre_municipio,
        MasterMunicipios.categoria_rural_urbana
    ).order_by(MasterMunicipios.nombre_municipio).all()
    
    return [
        {
            "codigo_dane": r.codigo_dane,
            "nombre": r.nombre_municipio,
            "categoria": r.categoria_rural_urbana
        }
        for r in results
    ]


@router.get("/categorias-delito")
async def get_categorias_delito(db: Session = Depends(get_db)):
    """
    Lista todas las categorias de delito disponibles.
    """
    results = db.query(
        FactSeguridad.categoria_delito
    ).distinct().filter(
        FactSeguridad.categoria_delito.isnot(None)
    ).order_by(FactSeguridad.categoria_delito).all()
    
    return [r.categoria_delito for r in results]


@router.get("/generos")
async def get_generos(db: Session = Depends(get_db)):
    """
    Lista todos los generos disponibles en los datos.
    """
    results = db.query(
        FactSeguridad.genero
    ).distinct().filter(
        FactSeguridad.genero.isnot(None)
    ).order_by(FactSeguridad.genero).all()
    
    return [r.genero for r in results]


@router.get("/grupos-etarios")
async def get_grupos_etarios(db: Session = Depends(get_db)):
    """
    Lista todos los grupos etarios disponibles.
    """
    results = db.query(
        FactSeguridad.grupo_etario
    ).distinct().filter(
        FactSeguridad.grupo_etario.isnot(None)
    ).order_by(FactSeguridad.grupo_etario).all()
    
    return [r.grupo_etario for r in results]


@router.get("/zonas")
async def get_zonas(db: Session = Depends(get_db)):
    """
    Lista todas las zonas disponibles (URBANA, RURAL, etc).
    """
    results = db.query(
        FactSeguridad.zona_hecho
    ).distinct().filter(
        FactSeguridad.zona_hecho.isnot(None)
    ).order_by(FactSeguridad.zona_hecho).all()
    
    return [r.zona_hecho for r in results]


@router.get("/armas-medios")
async def get_armas_medios(db: Session = Depends(get_db)):
    """
    Lista todas las armas/medios disponibles.
    """
    results = db.query(
        FactSeguridad.arma_medio
    ).distinct().filter(
        FactSeguridad.arma_medio.isnot(None)
    ).order_by(FactSeguridad.arma_medio).all()
    
    return [r.arma_medio for r in results]


@router.get("/modalidades")
async def get_modalidades(db: Session = Depends(get_db)):
    """
    Lista todas las modalidades especificas disponibles.
    """
    results = db.query(
        FactSeguridad.modalidad_especifica
    ).distinct().filter(
        FactSeguridad.modalidad_especifica.isnot(None)
    ).order_by(FactSeguridad.modalidad_especifica).all()
    
    return [r.modalidad_especifica for r in results]


@router.get("/anios")
async def get_anios(db: Session = Depends(get_db)):
    """
    Lista todos los años disponibles en los datos.
    """
    results = db.query(
        extract("year", FactSeguridad.fecha_hecho).label("anio")
    ).distinct().filter(
        FactSeguridad.fecha_hecho.isnot(None)
    ).order_by(
        extract("year", FactSeguridad.fecha_hecho).desc()
    ).all()
    
    return [int(r.anio) for r in results]


@router.get("/rango-fechas")
async def get_rango_fechas(db: Session = Depends(get_db)):
    """
    Retorna la fecha minima y maxima disponible en los datos.
    Util para configurar date pickers.
    """
    result = db.query(
        func.min(FactSeguridad.fecha_hecho).label("fecha_min"),
        func.max(FactSeguridad.fecha_hecho).label("fecha_max")
    ).filter(
        FactSeguridad.fecha_hecho.isnot(None)
    ).first()
    
    return {
        "fecha_minima": result.fecha_min.isoformat() if result.fecha_min else None,
        "fecha_maxima": result.fecha_max.isoformat() if result.fecha_max else None
    }


@router.get("/resumen")
async def get_resumen_filtros(db: Session = Depends(get_db)):
    """
    Retorna un resumen completo de todas las opciones disponibles.
    Util para inicializar todos los selectores de una vez.
    """
    # Municipios
    municipios = db.query(
        MasterMunicipios.nombre_municipio
    ).order_by(MasterMunicipios.nombre_municipio).all()
    
    # Categorias delito
    categorias = db.query(
        FactSeguridad.categoria_delito
    ).distinct().filter(
        FactSeguridad.categoria_delito.isnot(None)
    ).order_by(FactSeguridad.categoria_delito).all()
    
    # Generos
    generos = db.query(
        FactSeguridad.genero
    ).distinct().filter(
        FactSeguridad.genero.isnot(None)
    ).order_by(FactSeguridad.genero).all()
    
    # Grupos etarios
    grupos = db.query(
        FactSeguridad.grupo_etario
    ).distinct().filter(
        FactSeguridad.grupo_etario.isnot(None)
    ).order_by(FactSeguridad.grupo_etario).all()
    
    # Anios
    anios = db.query(
        extract("year", FactSeguridad.fecha_hecho).label("anio")
    ).distinct().filter(
        FactSeguridad.fecha_hecho.isnot(None)
    ).order_by(
        extract("year", FactSeguridad.fecha_hecho).desc()
    ).all()
    
    # Rango fechas
    fechas = db.query(
        func.min(FactSeguridad.fecha_hecho).label("min"),
        func.max(FactSeguridad.fecha_hecho).label("max")
    ).filter(
        FactSeguridad.fecha_hecho.isnot(None)
    ).first()
    
    return {
        "municipios": [r.nombre_municipio for r in municipios],
        "categorias_delito": [r.categoria_delito for r in categorias],
        "generos": [r.genero for r in generos],
        "grupos_etarios": [r.grupo_etario for r in grupos],
        "anios": [int(r.anio) for r in anios],
        "rango_fechas": {
            "minima": fechas.min.isoformat() if fechas.min else None,
            "maxima": fechas.max.isoformat() if fechas.max else None
        }
    }
