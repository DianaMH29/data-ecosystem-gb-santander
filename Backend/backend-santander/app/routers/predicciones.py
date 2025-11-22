"""
Router para predicciones de delitos.
Combina datos históricos con predicciones de ML.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import csv
import os

from ..database import get_db

router = APIRouter(
    prefix="/predicciones",
    tags=["Predicciones"]
)

# Ruta al archivo CSV de predicciones
PREDICCIONES_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "total_delitos_prediccion.csv")


def cargar_predicciones() -> dict:
    """
    Carga las predicciones del CSV en un diccionario.
    Estructura: {codigo_dane: [{anio, mes, prediccion}, ...]}
    """
    predicciones = {}
    
    try:
        with open(PREDICCIONES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                codigo_dane = int(row['codigo_dane_5d'])
                if codigo_dane not in predicciones:
                    predicciones[codigo_dane] = []
                
                predicciones[codigo_dane].append({
                    "anio": int(row['anio']),
                    "mes": int(row['mes']),
                    "total_delitos": round(float(row['pred_total_delitos']), 2),
                    "es_prediccion": True
                })
    except FileNotFoundError:
        return {}
    
    return predicciones


def resolver_municipio(db: Session, nombre: str) -> Optional[int]:
    """Resuelve el nombre de municipio a código DANE."""
    query = text("""
        SELECT codigo_dane FROM master_municipios 
        WHERE UPPER(nombre_municipio) LIKE UPPER(:nombre)
        LIMIT 1
    """)
    result = db.execute(query, {"nombre": f"%{nombre}%"}).fetchone()
    return result[0] if result else None


@router.get("/municipio/{municipio}")
def obtener_serie_temporal_municipio(
    municipio: str,
    db: Session = Depends(get_db),
    categoria_delito: Optional[str] = Query(None, description="Filtrar por categoría de delito"),
    incluir_prediccion: bool = Query(True, description="Incluir datos de predicción")
):
    """
    Obtiene la serie temporal completa de delitos por mes para un municipio,
    incluyendo datos históricos y predicciones futuras.
    
    Returns:
        - municipio: Nombre del municipio
        - codigo_dane: Código DANE
        - categoria_filtrada: Categoría de delito si se aplicó filtro
        - datos: Lista de {anio, mes, total_delitos, es_prediccion}
    """
    # Resolver municipio
    codigo_dane = resolver_municipio(db, municipio)
    if not codigo_dane:
        raise HTTPException(status_code=404, detail=f"Municipio '{municipio}' no encontrado")
    
    # Obtener nombre oficial
    nombre_query = text("SELECT nombre_municipio FROM master_municipios WHERE codigo_dane = :codigo")
    nombre_result = db.execute(nombre_query, {"codigo": codigo_dane}).fetchone()
    nombre_municipio = nombre_result[0] if nombre_result else municipio.upper()
    
    # Construir query para datos históricos
    where_clauses = ["codigo_dane = :codigo_dane"]
    params = {"codigo_dane": codigo_dane}
    
    if categoria_delito:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria_delito
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            EXTRACT(YEAR FROM fecha_hecho)::integer as anio,
            EXTRACT(MONTH FROM fecha_hecho)::integer as mes,
            COALESCE(SUM(cantidad), COUNT(*))::integer as total_delitos
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY EXTRACT(YEAR FROM fecha_hecho), EXTRACT(MONTH FROM fecha_hecho)
        ORDER BY anio, mes
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Construir lista de datos históricos
    datos = []
    for r in results:
        datos.append({
            "anio": r[0],
            "mes": r[1],
            "total_delitos": r[2],
            "es_prediccion": False
        })
    
    # Añadir predicciones si se solicita
    if incluir_prediccion:
        predicciones = cargar_predicciones()
        if codigo_dane in predicciones:
            # Filtrar predicciones que no estén ya en los datos históricos
            fechas_existentes = {(d["anio"], d["mes"]) for d in datos}
            
            for pred in predicciones[codigo_dane]:
                if (pred["anio"], pred["mes"]) not in fechas_existentes:
                    datos.append(pred)
    
    # Ordenar por fecha
    datos.sort(key=lambda x: (x["anio"], x["mes"]))
    
    return {
        "municipio": nombre_municipio,
        "codigo_dane": codigo_dane,
        "categoria_filtrada": categoria_delito.upper() if categoria_delito else None,
        "total_registros_historicos": sum(1 for d in datos if not d["es_prediccion"]),
        "total_predicciones": sum(1 for d in datos if d["es_prediccion"]),
        "datos": datos
    }


@router.get("/resumen")
def obtener_resumen_predicciones(
    db: Session = Depends(get_db),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    mes: Optional[int] = Query(None, description="Filtrar por mes (1-12)")
):
    """
    Obtiene un resumen de todas las predicciones disponibles.
    """
    predicciones = cargar_predicciones()
    
    # Obtener nombres de municipios
    nombres_query = text("SELECT codigo_dane, nombre_municipio FROM master_municipios")
    nombres_result = db.execute(nombres_query).fetchall()
    nombres_map = {r[0]: r[1] for r in nombres_result}
    
    resumen = []
    for codigo_dane, preds in predicciones.items():
        for pred in preds:
            # Aplicar filtros si existen
            if anio and pred["anio"] != anio:
                continue
            if mes and pred["mes"] != mes:
                continue
            
            resumen.append({
                "municipio": nombres_map.get(codigo_dane, f"CÓDIGO {codigo_dane}"),
                "codigo_dane": codigo_dane,
                "anio": pred["anio"],
                "mes": pred["mes"],
                "prediccion_delitos": pred["total_delitos"]
            })
    
    # Ordenar por predicción descendente
    resumen.sort(key=lambda x: x["prediccion_delitos"], reverse=True)
    
    return {
        "total_predicciones": len(resumen),
        "filtros": {
            "anio": anio,
            "mes": mes
        },
        "predicciones": resumen
    }


@router.get("/comparativa/{municipio}")
def obtener_comparativa_prediccion(
    municipio: str,
    db: Session = Depends(get_db)
):
    """
    Compara los datos históricos recientes con las predicciones
    para evaluar tendencias.
    """
    # Resolver municipio
    codigo_dane = resolver_municipio(db, municipio)
    if not codigo_dane:
        raise HTTPException(status_code=404, detail=f"Municipio '{municipio}' no encontrado")
    
    # Obtener nombre oficial
    nombre_query = text("SELECT nombre_municipio FROM master_municipios WHERE codigo_dane = :codigo")
    nombre_result = db.execute(nombre_query, {"codigo": codigo_dane}).fetchone()
    nombre_municipio = nombre_result[0] if nombre_result else municipio.upper()
    
    # Promedio mensual histórico (últimos 3 años)
    query_promedio = text("""
        SELECT 
            EXTRACT(MONTH FROM fecha_hecho)::integer as mes,
            COALESCE(SUM(cantidad), COUNT(*)) as total,
            COUNT(DISTINCT EXTRACT(YEAR FROM fecha_hecho)) as num_anios
        FROM fact_seguridad
        WHERE codigo_dane = :codigo_dane
          AND fecha_hecho >= CURRENT_DATE - INTERVAL '3 years'
        GROUP BY EXTRACT(MONTH FROM fecha_hecho)
        ORDER BY mes
    """)
    
    results = db.execute(query_promedio, {"codigo_dane": codigo_dane}).fetchall()
    promedios_historicos = {
        r[0]: round(r[1] / r[2], 2) if r[2] > 0 else 0 
        for r in results
    }
    
    # Obtener predicciones
    predicciones = cargar_predicciones()
    preds_municipio = predicciones.get(codigo_dane, [])
    
    comparativa = []
    for pred in preds_municipio:
        promedio_hist = promedios_historicos.get(pred["mes"], 0)
        diferencia = pred["total_delitos"] - promedio_hist
        porcentaje_cambio = round((diferencia / promedio_hist * 100), 2) if promedio_hist > 0 else None
        
        comparativa.append({
            "anio": pred["anio"],
            "mes": pred["mes"],
            "prediccion": pred["total_delitos"],
            "promedio_historico_mes": promedio_hist,
            "diferencia": round(diferencia, 2),
            "porcentaje_cambio": porcentaje_cambio,
            "tendencia": "AUMENTO" if diferencia > 0 else "DISMINUCIÓN" if diferencia < 0 else "ESTABLE"
        })
    
    comparativa.sort(key=lambda x: (x["anio"], x["mes"]))
    
    return {
        "municipio": nombre_municipio,
        "codigo_dane": codigo_dane,
        "nota": "El promedio histórico se calcula con los últimos 3 años de datos",
        "comparativa": comparativa
    }


@router.get("/alertas")
def obtener_alertas_prediccion(
    db: Session = Depends(get_db),
    umbral_aumento: float = Query(20.0, description="Porcentaje de aumento para generar alerta")
):
    """
    Identifica municipios con predicciones de aumento significativo de delitos.
    """
    predicciones = cargar_predicciones()
    
    # Obtener nombres de municipios
    nombres_query = text("SELECT codigo_dane, nombre_municipio FROM master_municipios")
    nombres_result = db.execute(nombres_query).fetchall()
    nombres_map = {r[0]: r[1] for r in nombres_result}
    
    alertas = []
    
    for codigo_dane, preds in predicciones.items():
        # Obtener promedio histórico del municipio
        query = text("""
            SELECT 
                EXTRACT(MONTH FROM fecha_hecho)::integer as mes,
                COALESCE(SUM(cantidad), COUNT(*)) as total,
                COUNT(DISTINCT EXTRACT(YEAR FROM fecha_hecho)) as num_anios
            FROM fact_seguridad
            WHERE codigo_dane = :codigo_dane
              AND fecha_hecho >= CURRENT_DATE - INTERVAL '3 years'
            GROUP BY EXTRACT(MONTH FROM fecha_hecho)
        """)
        
        results = db.execute(query, {"codigo_dane": codigo_dane}).fetchall()
        promedios = {r[0]: round(r[1] / r[2], 2) if r[2] > 0 else 0 for r in results}
        
        for pred in preds:
            promedio = promedios.get(pred["mes"], 0)
            if promedio > 0:
                porcentaje_cambio = ((pred["total_delitos"] - promedio) / promedio) * 100
                
                if porcentaje_cambio >= umbral_aumento:
                    alertas.append({
                        "municipio": nombres_map.get(codigo_dane, f"CÓDIGO {codigo_dane}"),
                        "codigo_dane": codigo_dane,
                        "anio": pred["anio"],
                        "mes": pred["mes"],
                        "prediccion": pred["total_delitos"],
                        "promedio_historico": promedio,
                        "porcentaje_aumento": round(porcentaje_cambio, 2),
                        "nivel_alerta": "CRÍTICO" if porcentaje_cambio >= 50 else "ALTO" if porcentaje_cambio >= 30 else "MODERADO"
                    })
    
    # Ordenar por porcentaje de aumento descendente
    alertas.sort(key=lambda x: x["porcentaje_aumento"], reverse=True)
    
    return {
        "umbral_configurado": umbral_aumento,
        "total_alertas": len(alertas),
        "alertas": alertas
    }
