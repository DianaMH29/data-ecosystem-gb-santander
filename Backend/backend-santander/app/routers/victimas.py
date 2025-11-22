"""
Seccion 3 - Victimas
- Barras por genero
- Barras por grupo etario
- Mapa de puntos con victimas (lat/lon)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional, List
from datetime import date
from ..database import get_db
from ..models import FactSeguridad
from ..utils import resolver_municipio

router = APIRouter(prefix="/victimas", tags=["Victimas"])


@router.get("/por-genero")
async def get_por_genero(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Tipo de delito: HURTO, VIF, SEXUAL, LESIONES, INFANCIA"),
    anio: Optional[int] = Query(None, description="Año (ej: 2024)"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    municipio: Optional[str] = Query(None, description="Nombre del municipio (ej: BUCARAMANGA)"),
):
    """
    Obtiene la distribucion de victimas por genero.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    query = db.query(
        FactSeguridad.genero.label("genero"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(
        FactSeguridad.genero.isnot(None)
    )
    
    if categoria_delito:
        query = query.filter(func.upper(FactSeguridad.categoria_delito) == categoria_delito.upper())
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if fecha_inicio:
        query = query.filter(FactSeguridad.fecha_hecho >= fecha_inicio)
    if fecha_fin:
        query = query.filter(FactSeguridad.fecha_hecho <= fecha_fin)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        FactSeguridad.genero
    ).order_by(
        func.sum(FactSeguridad.cantidad).desc()
    ).all()
    
    total_general = sum(int(r.total) for r in results)
    
    return [
        {
            "genero": r.genero,
            "total": int(r.total),
            "porcentaje": round((int(r.total) / total_general * 100), 2) if total_general > 0 else 0
        }
        for r in results
    ]


@router.get("/por-grupo-etario")
async def get_por_grupo_etario(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Tipo de delito: HURTO, VIF, SEXUAL, LESIONES, INFANCIA"),
    anio: Optional[int] = Query(None, description="Año (ej: 2024)"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    municipio: Optional[str] = Query(None, description="Nombre del municipio (ej: BUCARAMANGA)"),
):
    """
    Obtiene la distribucion de victimas por grupo etario.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    query = db.query(
        FactSeguridad.grupo_etario.label("grupo"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(
        FactSeguridad.grupo_etario.isnot(None)
    )
    
    if categoria_delito:
        query = query.filter(func.upper(FactSeguridad.categoria_delito) == categoria_delito.upper())
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if fecha_inicio:
        query = query.filter(FactSeguridad.fecha_hecho >= fecha_inicio)
    if fecha_fin:
        query = query.filter(FactSeguridad.fecha_hecho <= fecha_fin)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        FactSeguridad.grupo_etario
    ).order_by(
        func.sum(FactSeguridad.cantidad).desc()
    ).all()
    
    orden_grupos = ["MENOR", "ADOLESCENTE", "ADULTO"]
    resultado = [
        {
            "grupo_etario": r.grupo,
            "total": int(r.total)
        }
        for r in results
    ]
    
    def orden_key(x):
        g = x["grupo_etario"].upper() if x["grupo_etario"] else ""
        for i, og in enumerate(orden_grupos):
            if og in g:
                return i
        return len(orden_grupos)
    
    resultado.sort(key=orden_key)
    
    total_general = sum(r["total"] for r in resultado)
    for r in resultado:
        r["porcentaje"] = round((r["total"] / total_general * 100), 2) if total_general > 0 else 0
    
    return resultado


@router.get("/mapa-puntos")
async def get_mapa_puntos_victimas(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Tipo de delito: HURTO, VIF, SEXUAL, LESIONES, INFANCIA"),
    anio: Optional[int] = Query(None, description="Año (ej: 2024)"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    municipio: Optional[str] = Query(None, description="Nombre del municipio (ej: BUCARAMANGA)"),
    genero: Optional[str] = Query(None, description="Genero: MASCULINO, FEMENINO"),
    grupo_etario: Optional[str] = Query(None, description="Grupo etario: MENORES, ADOLESCENTES, ADULTOS"),
    limit: int = Query(5000, description="Limite de puntos a retornar"),
):
    """
    Obtiene puntos georreferenciados de victimas para visualizacion en mapa.
    Retorna GeoJSON con propiedades de cada evento.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    query = db.query(
        FactSeguridad.id_evento,
        FactSeguridad.fecha_hecho,
        FactSeguridad.categoria_delito,
        FactSeguridad.modalidad_especifica,
        FactSeguridad.zona_hecho,
        FactSeguridad.clase_sitio,
        FactSeguridad.genero,
        FactSeguridad.grupo_etario,
        FactSeguridad.arma_medio,
        FactSeguridad.cantidad,
        FactSeguridad.latitud,
        FactSeguridad.longitud,
    ).filter(
        FactSeguridad.latitud.isnot(None),
        FactSeguridad.longitud.isnot(None)
    )
    
    if categoria_delito:
        query = query.filter(func.upper(FactSeguridad.categoria_delito) == categoria_delito.upper())
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if fecha_inicio:
        query = query.filter(FactSeguridad.fecha_hecho >= fecha_inicio)
    if fecha_fin:
        query = query.filter(FactSeguridad.fecha_hecho <= fecha_fin)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    if genero:
        query = query.filter(func.upper(FactSeguridad.genero) == genero.upper())
    if grupo_etario:
        query = query.filter(func.upper(FactSeguridad.grupo_etario) == grupo_etario.upper())
    
    results = query.limit(limit).all()
    
    features = []
    for r in results:
        features.append({
            "type": "Feature",
            "properties": {
                "id_evento": r.id_evento,
                "fecha_hecho": r.fecha_hecho.isoformat() if r.fecha_hecho else None,
                "categoria_delito": r.categoria_delito,
                "modalidad_especifica": r.modalidad_especifica,
                "zona_hecho": r.zona_hecho,
                "clase_sitio": r.clase_sitio,
                "genero": r.genero,
                "grupo_etario": r.grupo_etario,
                "arma_medio": r.arma_medio,
                "cantidad": r.cantidad
            },
            "geometry": {
                "type": "Point",
                "coordinates": [r.longitud, r.latitud]
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "total_puntos": len(features)
    }


@router.get("/por-arma-medio")
async def get_por_arma_medio(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Tipo de delito"),
    anio: Optional[int] = Query(None, description="Año"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin"),
    municipio: Optional[str] = Query(None, description="Nombre del municipio"),
):
    """
    Obtiene la distribucion de eventos por arma/medio utilizado.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    query = db.query(
        FactSeguridad.arma_medio.label("arma_medio"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(
        FactSeguridad.arma_medio.isnot(None)
    )
    
    if categoria_delito:
        query = query.filter(func.upper(FactSeguridad.categoria_delito) == categoria_delito.upper())
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if fecha_inicio:
        query = query.filter(FactSeguridad.fecha_hecho >= fecha_inicio)
    if fecha_fin:
        query = query.filter(FactSeguridad.fecha_hecho <= fecha_fin)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        FactSeguridad.arma_medio
    ).order_by(
        func.sum(FactSeguridad.cantidad).desc()
    ).all()
    
    total_general = sum(int(r.total) for r in results)
    
    return [
        {
            "arma_medio": r.arma_medio,
            "total": int(r.total),
            "porcentaje": round((int(r.total) / total_general * 100), 2) if total_general > 0 else 0
        }
        for r in results
    ]


@router.get("/por-clase-sitio")
async def get_por_clase_sitio(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Tipo de delito"),
    anio: Optional[int] = Query(None, description="Año"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin"),
    municipio: Optional[str] = Query(None, description="Nombre del municipio"),
):
    """
    Obtiene la distribucion de eventos por clase de sitio.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    query = db.query(
        FactSeguridad.clase_sitio.label("clase_sitio"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(
        FactSeguridad.clase_sitio.isnot(None)
    )
    
    if categoria_delito:
        query = query.filter(func.upper(FactSeguridad.categoria_delito) == categoria_delito.upper())
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if fecha_inicio:
        query = query.filter(FactSeguridad.fecha_hecho >= fecha_inicio)
    if fecha_fin:
        query = query.filter(FactSeguridad.fecha_hecho <= fecha_fin)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        FactSeguridad.clase_sitio
    ).order_by(
        func.sum(FactSeguridad.cantidad).desc()
    ).all()
    
    total_general = sum(int(r.total) for r in results)
    
    return [
        {
            "clase_sitio": r.clase_sitio,
            "total": int(r.total),
            "porcentaje": round((int(r.total) / total_general * 100), 2) if total_general > 0 else 0
        }
        for r in results
    ]


@router.get("/genero-por-delito")
async def get_genero_por_delito(
    db: Session = Depends(get_db),
    anio: Optional[int] = Query(None, description="Año"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin"),
    municipio: Optional[str] = Query(None, description="Nombre del municipio"),
):
    """
    Obtiene la distribucion de genero por cada tipo de delito.
    Util para graficos de barras agrupadas.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    query = db.query(
        FactSeguridad.categoria_delito,
        FactSeguridad.genero,
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(
        FactSeguridad.categoria_delito.isnot(None),
        FactSeguridad.genero.isnot(None)
    )
    
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if fecha_inicio:
        query = query.filter(FactSeguridad.fecha_hecho >= fecha_inicio)
    if fecha_fin:
        query = query.filter(FactSeguridad.fecha_hecho <= fecha_fin)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        FactSeguridad.categoria_delito,
        FactSeguridad.genero
    ).order_by(
        FactSeguridad.categoria_delito,
        func.sum(FactSeguridad.cantidad).desc()
    ).all()
    
    delitos_dict = {}
    for r in results:
        if r.categoria_delito not in delitos_dict:
            delitos_dict[r.categoria_delito] = {}
        delitos_dict[r.categoria_delito][r.genero] = int(r.total)
    
    return [
        {
            "categoria_delito": delito,
            "generos": generos,
            "total": sum(generos.values())
        }
        for delito, generos in delitos_dict.items()
    ]


@router.get("/grupo-etario-por-delito")
async def get_grupo_etario_por_delito(
    db: Session = Depends(get_db),
    anio: Optional[int] = Query(None, description="Año"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin"),
    municipio: Optional[str] = Query(None, description="Nombre del municipio"),
):
    """
    Obtiene la distribucion de grupo etario por cada tipo de delito.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    query = db.query(
        FactSeguridad.categoria_delito,
        FactSeguridad.grupo_etario,
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(
        FactSeguridad.categoria_delito.isnot(None),
        FactSeguridad.grupo_etario.isnot(None)
    )
    
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if fecha_inicio:
        query = query.filter(FactSeguridad.fecha_hecho >= fecha_inicio)
    if fecha_fin:
        query = query.filter(FactSeguridad.fecha_hecho <= fecha_fin)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        FactSeguridad.categoria_delito,
        FactSeguridad.grupo_etario
    ).order_by(
        FactSeguridad.categoria_delito
    ).all()
    
    delitos_dict = {}
    for r in results:
        if r.categoria_delito not in delitos_dict:
            delitos_dict[r.categoria_delito] = {}
        delitos_dict[r.categoria_delito][r.grupo_etario] = int(r.total)
    
    return [
        {
            "categoria_delito": delito,
            "grupos_etarios": grupos,
            "total": sum(grupos.values())
        }
        for delito, grupos in delitos_dict.items()
    ]
