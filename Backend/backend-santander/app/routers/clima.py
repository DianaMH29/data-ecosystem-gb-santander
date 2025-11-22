"""
Sección 4 — Clima
- Scatter lluvia vs hurto
- Barras lluvia por categorías
- Línea de tiempo: lluvia y delitos superpuestos
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from typing import Optional, List
from ..database import get_db
from ..models import FactClima, FactSeguridad

router = APIRouter(prefix="/clima", tags=["Clima"])


@router.get("/scatter-lluvia-delitos")
async def get_scatter_lluvia_delitos(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query("HURTO", description="Tipo de delito a correlacionar"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Obtiene datos para scatter plot: precipitación diaria vs cantidad de delitos.
    Cada punto es un día con su precipitación y conteo de delitos.
    """
    # Subquery para delitos por día
    delitos_subq = db.query(
        FactSeguridad.fecha_hecho.label("fecha"),
        func.coalesce(func.sum(FactSeguridad.cantidad), 0).label("total_delitos")
    ).filter(FactSeguridad.fecha_hecho.isnot(None))
    
    if categoria_delito:
        delitos_subq = delitos_subq.filter(FactSeguridad.categoria_delito == categoria_delito)
    if anio:
        delitos_subq = delitos_subq.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if codigo_dane:
        delitos_subq = delitos_subq.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    delitos_subq = delitos_subq.group_by(FactSeguridad.fecha_hecho).subquery()
    
    # Query clima
    clima_query = db.query(
        FactClima.fecha,
        FactClima.precipitacion_mm
    )
    
    if anio:
        clima_query = clima_query.filter(extract("year", FactClima.fecha) == anio)
    if codigo_dane:
        clima_query = clima_query.filter(FactClima.codigo_dane == codigo_dane)
    
    # JOIN con delitos
    query = db.query(
        FactClima.fecha,
        FactClima.precipitacion_mm,
        func.coalesce(delitos_subq.c.total_delitos, 0).label("total_delitos")
    ).outerjoin(
        delitos_subq,
        FactClima.fecha == delitos_subq.c.fecha
    )
    
    if anio:
        query = query.filter(extract("year", FactClima.fecha) == anio)
    if codigo_dane:
        query = query.filter(FactClima.codigo_dane == codigo_dane)
    
    results = query.order_by(FactClima.fecha).all()
    
    return [
        {
            "fecha": r.fecha.isoformat() if r.fecha else None,
            "precipitacion_mm": float(r.precipitacion_mm) if r.precipitacion_mm else 0,
            "total_delitos": int(r.total_delitos)
        }
        for r in results
    ]


@router.get("/barras-categorias-lluvia")
async def get_barras_categorias_lluvia(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query("HURTO", description="Tipo de delito"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Agrupa delitos por categorías de precipitación:
    - Sin lluvia (0 mm)
    - Lluvia ligera (0.1-5 mm)
    - Lluvia moderada (5-20 mm)
    - Lluvia fuerte (>20 mm)
    """
    # Subquery para delitos por día
    delitos_subq = db.query(
        FactSeguridad.fecha_hecho.label("fecha"),
        func.coalesce(func.sum(FactSeguridad.cantidad), 0).label("total_delitos")
    ).filter(FactSeguridad.fecha_hecho.isnot(None))
    
    if categoria_delito:
        delitos_subq = delitos_subq.filter(FactSeguridad.categoria_delito == categoria_delito)
    if anio:
        delitos_subq = delitos_subq.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if codigo_dane:
        delitos_subq = delitos_subq.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    delitos_subq = delitos_subq.group_by(FactSeguridad.fecha_hecho).subquery()
    
    # Categorizar precipitación
    categoria_lluvia = case(
        (FactClima.precipitacion_mm == 0, "Sin lluvia"),
        (FactClima.precipitacion_mm <= 5, "Lluvia ligera"),
        (FactClima.precipitacion_mm <= 20, "Lluvia moderada"),
        else_="Lluvia fuerte"
    ).label("categoria_lluvia")
    
    query = db.query(
        categoria_lluvia,
        func.count().label("dias"),
        func.sum(func.coalesce(delitos_subq.c.total_delitos, 0)).label("total_delitos"),
        func.avg(func.coalesce(delitos_subq.c.total_delitos, 0)).label("promedio_delitos")
    ).outerjoin(
        delitos_subq,
        FactClima.fecha == delitos_subq.c.fecha
    )
    
    if anio:
        query = query.filter(extract("year", FactClima.fecha) == anio)
    if codigo_dane:
        query = query.filter(FactClima.codigo_dane == codigo_dane)
    
    results = query.group_by(categoria_lluvia).all()
    
    # Ordenar categorías
    orden = ["Sin lluvia", "Lluvia ligera", "Lluvia moderada", "Lluvia fuerte"]
    resultado = [
        {
            "categoria_lluvia": r.categoria_lluvia,
            "dias": int(r.dias),
            "total_delitos": int(r.total_delitos) if r.total_delitos else 0,
            "promedio_delitos_dia": round(float(r.promedio_delitos), 2) if r.promedio_delitos else 0
        }
        for r in results
    ]
    resultado.sort(key=lambda x: orden.index(x["categoria_lluvia"]) if x["categoria_lluvia"] in orden else 4)
    
    return resultado


@router.get("/linea-tiempo-superpuesta")
async def get_linea_tiempo_superpuesta(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query("HURTO", description="Tipo de delito"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
    agrupacion: str = Query("mensual", description="Agrupación: 'diaria', 'semanal', 'mensual'"),
):
    """
    Obtiene serie temporal de lluvia y delitos para visualización superpuesta.
    Permite ver correlación temporal entre precipitación y delincuencia.
    """
    # Determinar agrupación
    if agrupacion == "diaria":
        grupo_clima = FactClima.fecha
        grupo_delitos = FactSeguridad.fecha_hecho
        orden = FactClima.fecha
    elif agrupacion == "semanal":
        grupo_clima = func.date_trunc("week", FactClima.fecha)
        grupo_delitos = func.date_trunc("week", FactSeguridad.fecha_hecho)
        orden = func.date_trunc("week", FactClima.fecha)
    else:  # mensual
        grupo_clima = func.date_trunc("month", FactClima.fecha)
        grupo_delitos = func.date_trunc("month", FactSeguridad.fecha_hecho)
        orden = func.date_trunc("month", FactClima.fecha)
    
    # Query para clima
    clima_query = db.query(
        grupo_clima.label("periodo"),
        func.avg(FactClima.precipitacion_mm).label("precipitacion_promedio"),
        func.sum(FactClima.precipitacion_mm).label("precipitacion_total")
    )
    
    if anio:
        clima_query = clima_query.filter(extract("year", FactClima.fecha) == anio)
    if codigo_dane:
        clima_query = clima_query.filter(FactClima.codigo_dane == codigo_dane)
    
    clima_results = clima_query.group_by(grupo_clima).order_by(orden).all()
    
    # Query para delitos
    delitos_query = db.query(
        grupo_delitos.label("periodo"),
        func.sum(FactSeguridad.cantidad).label("total_delitos")
    ).filter(FactSeguridad.fecha_hecho.isnot(None))
    
    if categoria_delito:
        delitos_query = delitos_query.filter(FactSeguridad.categoria_delito == categoria_delito)
    if anio:
        delitos_query = delitos_query.filter(extract("year", FactSeguridad.fecha_hecho) == anio)
    if codigo_dane:
        delitos_query = delitos_query.filter(FactSeguridad.codigo_dane == codigo_dane)
    
    delitos_results = delitos_query.group_by(grupo_delitos).all()
    delitos_dict = {r.periodo: int(r.total_delitos) for r in delitos_results}
    
    # Combinar resultados
    data = []
    for r in clima_results:
        periodo = r.periodo
        data.append({
            "periodo": periodo.isoformat() if hasattr(periodo, "isoformat") else str(periodo),
            "precipitacion_promedio": round(float(r.precipitacion_promedio), 2) if r.precipitacion_promedio else 0,
            "precipitacion_total": round(float(r.precipitacion_total), 2) if r.precipitacion_total else 0,
            "total_delitos": delitos_dict.get(periodo, 0)
        })
    
    return {
        "agrupacion": agrupacion,
        "categoria_delito": categoria_delito,
        "data": data
    }


@router.get("/correlacion")
async def get_correlacion_lluvia_delitos(
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query("HURTO", description="Tipo de delito"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Calcula estadísticas de correlación entre lluvia y delitos.
    """
    # Obtener datos del scatter
    scatter_data = await get_scatter_lluvia_delitos(
        db=db, 
        categoria_delito=categoria_delito,
        anio=anio,
        codigo_dane=codigo_dane
    )
    
    if not scatter_data:
        return {"mensaje": "No hay datos suficientes para calcular correlación"}
    
    # Calcular correlación de Pearson manualmente
    precipitaciones = [d["precipitacion_mm"] for d in scatter_data]
    delitos = [d["total_delitos"] for d in scatter_data]
    
    n = len(precipitaciones)
    if n < 2:
        return {"mensaje": "No hay suficientes puntos de datos"}
    
    # Media
    mean_precip = sum(precipitaciones) / n
    mean_delitos = sum(delitos) / n
    
    # Covarianza y desviaciones estándar
    cov = sum((p - mean_precip) * (d - mean_delitos) for p, d in zip(precipitaciones, delitos)) / n
    std_precip = (sum((p - mean_precip) ** 2 for p in precipitaciones) / n) ** 0.5
    std_delitos = (sum((d - mean_delitos) ** 2 for d in delitos) / n) ** 0.5
    
    # Correlación
    if std_precip > 0 and std_delitos > 0:
        correlacion = cov / (std_precip * std_delitos)
    else:
        correlacion = 0
    
    return {
        "categoria_delito": categoria_delito,
        "n_observaciones": n,
        "precipitacion_promedio": round(mean_precip, 2),
        "delitos_promedio": round(mean_delitos, 2),
        "correlacion_pearson": round(correlacion, 4),
        "interpretacion": (
            "Correlación fuerte positiva" if correlacion > 0.7 else
            "Correlación moderada positiva" if correlacion > 0.3 else
            "Correlación débil positiva" if correlacion > 0 else
            "Correlación débil negativa" if correlacion > -0.3 else
            "Correlación moderada negativa" if correlacion > -0.7 else
            "Correlación fuerte negativa"
        )
    }


@router.get("/resumen-precipitacion")
async def get_resumen_precipitacion(
    db: Session = Depends(get_db),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    codigo_dane: Optional[int] = Query(None, description="Filtrar por municipio"),
):
    """
    Obtiene estadísticas resumidas de precipitación.
    """
    query = db.query(
        func.count().label("dias_con_registro"),
        func.sum(case((FactClima.precipitacion_mm == 0, 1), else_=0)).label("dias_secos"),
        func.sum(case((FactClima.precipitacion_mm > 0, 1), else_=0)).label("dias_con_lluvia"),
        func.avg(FactClima.precipitacion_mm).label("precipitacion_promedio"),
        func.max(FactClima.precipitacion_mm).label("precipitacion_maxima"),
        func.sum(FactClima.precipitacion_mm).label("precipitacion_total")
    )
    
    if anio:
        query = query.filter(extract("year", FactClima.fecha) == anio)
    if codigo_dane:
        query = query.filter(FactClima.codigo_dane == codigo_dane)
    
    result = query.first()
    
    return {
        "dias_con_registro": int(result.dias_con_registro) if result.dias_con_registro else 0,
        "dias_secos": int(result.dias_secos) if result.dias_secos else 0,
        "dias_con_lluvia": int(result.dias_con_lluvia) if result.dias_con_lluvia else 0,
        "precipitacion_promedio_mm": round(float(result.precipitacion_promedio), 2) if result.precipitacion_promedio else 0,
        "precipitacion_maxima_mm": round(float(result.precipitacion_maxima), 2) if result.precipitacion_maxima else 0,
        "precipitacion_total_mm": round(float(result.precipitacion_total), 2) if result.precipitacion_total else 0
    }
