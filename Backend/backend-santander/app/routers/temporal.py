"""
Seccion 2 - Temporal
- Linea mensual de hurtos
- Linea anual
- Barras por dia de semana (calculado desde fecha_hecho)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional, List
from ..database import get_db
from ..models import FactSeguridad

router = APIRouter(prefix="/temporal", tags=["Temporal"])


@router.get("/linea-mensual")
async def get_linea_mensual(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito (ej: HURTO)"),
    anio: Optional[int] = Query(None, description="Filtrar por anio especifico"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Obtiene la serie temporal mensual de delitos.
    Ideal para graficos de linea.
    """
    query = db.query(
        extract("year", FactSeguridad.fecha_hecho).label("anio"),
        extract("month", FactSeguridad.fecha_hecho).label("mes"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(FactSeguridad.fecha_hecho.isnot(None))
    
    if categoria_delito:
        query = query.filter(FactSeguridad.categoria_delito == categoria_delito)
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        extract("year", FactSeguridad.fecha_hecho),
        extract("month", FactSeguridad.fecha_hecho)
    ).order_by(
        extract("year", FactSeguridad.fecha_hecho),
        extract("month", FactSeguridad.fecha_hecho)
    ).all()
    
    return [
        {
            "anio": int(r.anio),
            "mes": int(r.mes),
            "periodo": f"{int(r.anio)}-{int(r.mes):02d}",
            "total": int(r.total)
        }
        for r in results
    ]


@router.get("/linea-anual")
async def get_linea_anual(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Obtiene la serie temporal anual de delitos.
    """
    query = db.query(
        extract("year", FactSeguridad.fecha_hecho).label("anio"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(FactSeguridad.fecha_hecho.isnot(None))
    
    if categoria_delito:
        query = query.filter(FactSeguridad.categoria_delito == categoria_delito)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        extract("year", FactSeguridad.fecha_hecho)
    ).order_by(
        extract("year", FactSeguridad.fecha_hecho)
    ).all()
    
    return [
        {
            "anio": int(r.anio),
            "total": int(r.total)
        }
        for r in results
    ]


@router.get("/por-dia-semana")
async def get_por_dia_semana(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito"),
    anio: Optional[int] = Query(None, description="Filtrar por anio"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Obtiene la distribucion de delitos por dia de la semana.
    Se calcula desde fecha_hecho usando EXTRACT(DOW).
    PostgreSQL: DOW returns 0=Sunday to 6=Saturday
    """
    dias_nombre = {
        0: "DOMINGO", 1: "LUNES", 2: "MARTES", 3: "MIERCOLES",
        4: "JUEVES", 5: "VIERNES", 6: "SABADO"
    }
    
    query = db.query(
        extract("dow", FactSeguridad.fecha_hecho).label("dia_num"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(FactSeguridad.fecha_hecho.isnot(None))
    
    if categoria_delito:
        query = query.filter(FactSeguridad.categoria_delito == categoria_delito)
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        extract("dow", FactSeguridad.fecha_hecho)
    ).order_by(
        extract("dow", FactSeguridad.fecha_hecho)
    ).all()
    
    resultado = [
        {
            "dia": dias_nombre.get(int(r.dia_num), f"DIA_{int(r.dia_num)}"),
            "dia_num": int(r.dia_num),
            "total": int(r.total)
        }
        for r in results
    ]
    
    orden_lunes_primero = [1, 2, 3, 4, 5, 6, 0]
    resultado.sort(key=lambda x: orden_lunes_primero.index(x["dia_num"]) if x["dia_num"] in orden_lunes_primero else 7)
    
    return resultado


@router.get("/tendencia-semanal")
async def get_tendencia_semanal(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito"),
    anio: Optional[int] = Query(None, description="Filtrar por anio"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Obtiene la serie temporal semanal de delitos.
    """
    query = db.query(
        extract("year", FactSeguridad.fecha_hecho).label("anio"),
        extract("week", FactSeguridad.fecha_hecho).label("semana"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(FactSeguridad.fecha_hecho.isnot(None))
    
    if categoria_delito:
        query = query.filter(FactSeguridad.categoria_delito == categoria_delito)
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        extract("year", FactSeguridad.fecha_hecho),
        extract("week", FactSeguridad.fecha_hecho)
    ).order_by(
        extract("year", FactSeguridad.fecha_hecho),
        extract("week", FactSeguridad.fecha_hecho)
    ).all()
    
    return [
        {
            "anio": int(r.anio),
            "semana": int(r.semana),
            "periodo": f"{int(r.anio)}-W{int(r.semana):02d}",
            "total": int(r.total)
        }
        for r in results
    ]


@router.get("/comparativa-anual")
async def get_comparativa_anual(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Compara la evolucion mensual entre anios.
    Util para ver estacionalidad y tendencias interanuales.
    """
    query = db.query(
        extract("year", FactSeguridad.fecha_hecho).label("anio"),
        extract("month", FactSeguridad.fecha_hecho).label("mes"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(FactSeguridad.fecha_hecho.isnot(None))
    
    if categoria_delito:
        query = query.filter(FactSeguridad.categoria_delito == categoria_delito)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        extract("year", FactSeguridad.fecha_hecho),
        extract("month", FactSeguridad.fecha_hecho)
    ).order_by(
        extract("year", FactSeguridad.fecha_hecho),
        extract("month", FactSeguridad.fecha_hecho)
    ).all()
    
    datos_por_anio = {}
    for r in results:
        anio = int(r.anio)
        if anio not in datos_por_anio:
            datos_por_anio[anio] = {}
        datos_por_anio[anio][int(r.mes)] = int(r.total)
    
    return {
        "anios": list(datos_por_anio.keys()),
        "datos": datos_por_anio
    }


@router.get("/por-modalidad")
async def get_por_modalidad(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito"),
    anio: Optional[int] = Query(None, description="Filtrar por anio"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Obtiene la distribucion de delitos por modalidad especifica.
    """
    query = db.query(
        FactSeguridad.modalidad_especifica.label("modalidad"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(
        FactSeguridad.modalidad_especifica.isnot(None)
    )
    
    if categoria_delito:
        query = query.filter(FactSeguridad.categoria_delito == categoria_delito)
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        FactSeguridad.modalidad_especifica
    ).order_by(
        func.sum(FactSeguridad.cantidad).desc()
    ).all()
    
    total_general = sum(int(r.total) for r in results)
    
    return [
        {
            "modalidad": r.modalidad,
            "total": int(r.total),
            "porcentaje": round((int(r.total) / total_general * 100), 2) if total_general > 0 else 0
        }
        for r in results
    ]


@router.get("/por-zona")
async def get_por_zona(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por tipo de delito"),
    anio: Optional[int] = Query(None, description="Filtrar por anio"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Obtiene la distribucion de delitos por zona (URBANA/RURAL).
    """
    query = db.query(
        FactSeguridad.zona_hecho.label("zona"),
        func.sum(FactSeguridad.cantidad).label("total")
    ).filter(
        FactSeguridad.zona_hecho.isnot(None)
    )
    
    if categoria_delito:
        query = query.filter(FactSeguridad.categoria_delito == categoria_delito)
    if anio:
        query = query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if codigo_dane:
        query = query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    results = query.group_by(
        FactSeguridad.zona_hecho
    ).order_by(
        func.sum(FactSeguridad.cantidad).desc()
    ).all()
    
    total_general = sum(int(r.total) for r in results)
    
    return [
        {
            "zona": r.zona,
            "total": int(r.total),
            "porcentaje": round((int(r.total) / total_general * 100), 2) if total_general > 0 else 0
        }
        for r in results
    ]


@router.get("/anios-disponibles")
async def get_anios_disponibles(db: Session = Depends(get_db)):
    """
    Lista todos los anios disponibles en los datos.
    """
    results = db.query(
        extract("year", FactSeguridad.fecha_hecho).label("anio")
    ).distinct().filter(
        FactSeguridad.fecha_hecho.isnot(None)
    ).order_by(
        extract("year", FactSeguridad.fecha_hecho)
    ).all()
    
    return [int(r.anio) for r in results]
