"""
Sección 1 — Geografía
- Mapa coroplético: delitos totales por municipio
- Mapa coroplético: tasa por 100.000 habitantes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional, List
from ..database import get_db
from ..models import FactSeguridad, MasterMunicipios, MasterDemografia

router = APIRouter(prefix="/geografia", tags=["Geografía"])


@router.get("/delitos-por-municipio")
async def get_delitos_por_municipio(
    db: Session = Depends(get_db),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito"),
):
    """
    Obtiene el total de delitos por municipio con geometría GeoJSON
    para visualización en mapa coroplético.
    """
    # Base query
    query = db.query(
        MasterMunicipios.codigo_dane,
        MasterMunicipios.nombre_municipio,
        MasterMunicipios.categoria_rural_urbana,
        func.ST_AsGeoJSON(MasterMunicipios.geom).label("geojson"),
        func.coalesce(func.sum(FactSeguridad.cantidad), 0).label("total_delitos")
    ).outerjoin(
        FactSeguridad,
        MasterMunicipios.codigo_dane == FactSeguridad.codigo_dane
    )
    
    # Aplicar filtros
    if anio:
        query = query.filter(func.extract("year", FactSeguridad.fecha_hecho) == anio)
    if categoria_delito:
        query = query.filter(FactSeguridad.categoria_delito == categoria_delito)
    
    # Agrupar y ejecutar
    results = query.group_by(
        MasterMunicipios.codigo_dane,
        MasterMunicipios.nombre_municipio,
        MasterMunicipios.categoria_rural_urbana,
        MasterMunicipios.geom
    ).all()
    
    # Formatear respuesta GeoJSON
    features = []
    for row in results:
        import json
        geom = json.loads(row.geojson) if row.geojson else None
        features.append({
            "type": "Feature",
            "properties": {
                "codigo_dane": row.codigo_dane,
                "nombre_municipio": row.nombre_municipio,
                "categoria_rural_urbana": row.categoria_rural_urbana,
                "total_delitos": int(row.total_delitos)
            },
            "geometry": geom
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/tasa-por-municipio")
async def get_tasa_por_municipio(
    db: Session = Depends(get_db),
    anio: Optional[int] = Query(None, description="Año para población y delitos"),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito"),
):
    """
    Obtiene la tasa de delitos por 100.000 habitantes por municipio.
    Tasa = (delitos / población) * 100.000
    """
    # Subquery para contar delitos por municipio
    delitos_subq = db.query(
        FactSeguridad.codigo_dane,
        func.coalesce(func.sum(FactSeguridad.cantidad), 0).label("total_delitos")
    )
    
    if anio:
        delitos_subq = delitos_subq.filter(
            func.extract("year", FactSeguridad.fecha_hecho) == anio
        )
    if categoria_delito:
        delitos_subq = delitos_subq.filter(
            FactSeguridad.categoria_delito == categoria_delito
        )
    
    delitos_subq = delitos_subq.group_by(FactSeguridad.codigo_dane).subquery()
    
    # Query principal con demografía
    query = db.query(
        MasterMunicipios.codigo_dane,
        MasterMunicipios.nombre_municipio,
        MasterMunicipios.categoria_rural_urbana,
        func.ST_AsGeoJSON(MasterMunicipios.geom).label("geojson"),
        MasterDemografia.poblacion_total,
        func.coalesce(delitos_subq.c.total_delitos, 0).label("total_delitos")
    ).outerjoin(
        MasterDemografia,
        MasterMunicipios.codigo_dane == MasterDemografia.codigo_dane
    ).outerjoin(
        delitos_subq,
        MasterMunicipios.codigo_dane == delitos_subq.c.codigo_dane
    )
    
    if anio:
        query = query.filter(MasterDemografia.anio == anio)
    
    results = query.all()
    
    # Calcular tasa y formatear GeoJSON
    features = []
    for row in results:
        import json
        geom = json.loads(row.geojson) if row.geojson else None
        poblacion = row.poblacion_total or 1  # Evitar división por cero
        total_delitos = int(row.total_delitos) if row.total_delitos else 0
        tasa = (total_delitos / poblacion) * 100000 if poblacion > 0 else 0
        
        features.append({
            "type": "Feature",
            "properties": {
                "codigo_dane": row.codigo_dane,
                "nombre_municipio": row.nombre_municipio,
                "categoria_rural_urbana": row.categoria_rural_urbana,
                "total_delitos": total_delitos,
                "poblacion_total": poblacion,
                "tasa_por_100k": round(tasa, 2)
            },
            "geometry": geom
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/municipios")
async def get_municipios(db: Session = Depends(get_db)):
    """
    Lista todos los municipios disponibles (sin geometría, para selectores).
    """
    results = db.query(
        MasterMunicipios.codigo_dane,
        MasterMunicipios.nombre_municipio,
        MasterMunicipios.categoria_rural_urbana
    ).order_by(MasterMunicipios.nombre_municipio).all()
    
    return [
        {
            "codigo_dane": r.codigo_dane,
            "nombre_municipio": r.nombre_municipio,
            "categoria_rural_urbana": r.categoria_rural_urbana
        }
        for r in results
    ]


@router.get("/categorias-delito")
async def get_categorias_delito(db: Session = Depends(get_db)):
    """
    Lista todas las categorías de delito disponibles.
    """
    results = db.query(
        FactSeguridad.categoria_delito
    ).distinct().filter(
        FactSeguridad.categoria_delito.isnot(None)
    ).order_by(FactSeguridad.categoria_delito).all()
    
    return [r.categoria_delito for r in results]
