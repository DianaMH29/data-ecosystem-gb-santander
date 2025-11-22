"""
Módulo de Consultas Climáticas del Chatbot
Correlación entre precipitación y delitos
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from .chatbot_base import resolver_municipio, obtener_nombre_municipio


def obtener_correlacion_clima_delitos(
    db: Session,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Analiza la correlación entre precipitación y eventos de seguridad.
    Compara los días con lluvia vs días sin lluvia.
    """
    where_clauses = ["fc.precipitacion_mm IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("fs.codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if categoria:
        where_clauses.append("UPPER(fs.categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    # Análisis de eventos por condición de lluvia
    query = text(f"""
        WITH eventos_clima AS (
            SELECT 
                fs.id_evento,
                fs.categoria_delito,
                fs.fecha_hecho,
                fc.precipitacion_mm,
                CASE 
                    WHEN fc.precipitacion_mm = 0 THEN 'SIN_LLUVIA'
                    WHEN fc.precipitacion_mm < 5 THEN 'LLUVIA_LIGERA'
                    WHEN fc.precipitacion_mm < 20 THEN 'LLUVIA_MODERADA'
                    ELSE 'LLUVIA_FUERTE'
                END as condicion_lluvia
            FROM fact_seguridad fs
            JOIN fact_clima fc ON fs.codigo_dane = fc.codigo_dane 
                AND fs.fecha_hecho::date = fc.fecha::date
            WHERE {where_sql}
        )
        SELECT 
            condicion_lluvia,
            COUNT(*) as total_eventos,
            AVG(precipitacion_mm) as promedio_precipitacion
        FROM eventos_clima
        GROUP BY condicion_lluvia
        ORDER BY total_eventos DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Promedio de delitos por día según condición
    query_promedio_diario = text(f"""
        WITH dias_clima AS (
            SELECT 
                fc.fecha,
                fc.codigo_dane,
                fc.precipitacion_mm,
                CASE 
                    WHEN fc.precipitacion_mm = 0 THEN 'SIN_LLUVIA'
                    WHEN fc.precipitacion_mm < 5 THEN 'LLUVIA_LIGERA'
                    WHEN fc.precipitacion_mm < 20 THEN 'LLUVIA_MODERADA'
                    ELSE 'LLUVIA_FUERTE'
                END as condicion_lluvia
            FROM fact_clima fc
            WHERE fc.precipitacion_mm IS NOT NULL
        ),
        eventos_por_dia AS (
            SELECT 
                dc.fecha,
                dc.condicion_lluvia,
                dc.precipitacion_mm,
                COUNT(fs.id_evento) as eventos_dia
            FROM dias_clima dc
            LEFT JOIN fact_seguridad fs ON dc.codigo_dane = fs.codigo_dane 
                AND dc.fecha = fs.fecha_hecho::date
                {"AND UPPER(fs.categoria_delito) = UPPER(:categoria)" if categoria else ""}
            {"WHERE dc.codigo_dane = :codigo_dane" if municipio and codigo_dane else ""}
            GROUP BY dc.fecha, dc.condicion_lluvia, dc.precipitacion_mm
        )
        SELECT 
            condicion_lluvia,
            COUNT(*) as total_dias,
            SUM(eventos_dia) as total_eventos,
            ROUND(AVG(eventos_dia)::numeric, 2) as promedio_eventos_dia,
            ROUND(AVG(precipitacion_mm)::numeric, 2) as promedio_precipitacion
        FROM eventos_por_dia
        GROUP BY condicion_lluvia
        ORDER BY promedio_eventos_dia DESC
    """)
    
    results_promedio = db.execute(query_promedio_diario, params).fetchall()
    
    # Correlación por categoría de delito
    query_por_categoria = text(f"""
        WITH eventos_clima AS (
            SELECT 
                fs.categoria_delito,
                fc.precipitacion_mm,
                CASE 
                    WHEN fc.precipitacion_mm = 0 THEN 'SIN_LLUVIA'
                    ELSE 'CON_LLUVIA'
                END as tiene_lluvia
            FROM fact_seguridad fs
            JOIN fact_clima fc ON fs.codigo_dane = fc.codigo_dane 
                AND fs.fecha_hecho::date = fc.fecha::date
            WHERE fc.precipitacion_mm IS NOT NULL
            {"AND fs.codigo_dane = :codigo_dane" if municipio and codigo_dane else ""}
        )
        SELECT 
            categoria_delito,
            tiene_lluvia,
            COUNT(*) as total_eventos
        FROM eventos_clima
        GROUP BY categoria_delito, tiene_lluvia
        ORDER BY categoria_delito, tiene_lluvia
    """)
    
    results_categoria = db.execute(query_por_categoria, params).fetchall()
    
    # Procesar resultados por categoría
    categorias_dict = {}
    for r in results_categoria:
        cat = r[0]
        if cat not in categorias_dict:
            categorias_dict[cat] = {"con_lluvia": 0, "sin_lluvia": 0}
        if r[1] == "CON_LLUVIA":
            categorias_dict[cat]["con_lluvia"] = r[2]
        else:
            categorias_dict[cat]["sin_lluvia"] = r[2]
    
    categorias_comparacion = []
    for cat, valores in categorias_dict.items():
        total = valores["con_lluvia"] + valores["sin_lluvia"]
        if total > 0:
            categorias_comparacion.append({
                "categoria": cat,
                "con_lluvia": valores["con_lluvia"],
                "sin_lluvia": valores["sin_lluvia"],
                "porcentaje_con_lluvia": round(valores["con_lluvia"] / total * 100, 2),
                "porcentaje_sin_lluvia": round(valores["sin_lluvia"] / total * 100, 2)
            })
    
    return {
        "descripcion": "Análisis de correlación entre precipitación y eventos de seguridad",
        "periodo_datos_clima": "2005-2019",
        "filtros": {
            "municipio": municipio,
            "categoria": categoria
        },
        "distribucion_por_condicion": [
            {
                "condicion": r[0],
                "total_eventos": r[1],
                "promedio_precipitacion_mm": float(r[2]) if r[2] else 0
            }
            for r in results
        ],
        "promedio_diario_por_condicion": [
            {
                "condicion": r[0],
                "total_dias": r[1],
                "total_eventos": r[2],
                "promedio_eventos_por_dia": float(r[3]) if r[3] else 0,
                "promedio_precipitacion_mm": float(r[4]) if r[4] else 0
            }
            for r in results_promedio
        ],
        "comparacion_por_categoria": categorias_comparacion
    }


def obtener_eventos_por_precipitacion(
    db: Session,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Analiza los eventos de seguridad según rangos de precipitación.
    """
    where_clauses = ["fc.precipitacion_mm IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("fs.codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if categoria:
        where_clauses.append("UPPER(fs.categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            CASE 
                WHEN fc.precipitacion_mm = 0 THEN '0 mm (Seco)'
                WHEN fc.precipitacion_mm < 2 THEN '0.1-2 mm (Muy ligera)'
                WHEN fc.precipitacion_mm < 5 THEN '2-5 mm (Ligera)'
                WHEN fc.precipitacion_mm < 10 THEN '5-10 mm (Moderada)'
                WHEN fc.precipitacion_mm < 20 THEN '10-20 mm (Fuerte)'
                ELSE '20+ mm (Muy fuerte)'
            END as rango_precipitacion,
            COUNT(*) as total_eventos,
            MIN(fc.precipitacion_mm) as min_precipitacion,
            MAX(fc.precipitacion_mm) as max_precipitacion,
            ROUND(AVG(fc.precipitacion_mm)::numeric, 2) as promedio_precipitacion
        FROM fact_seguridad fs
        JOIN fact_clima fc ON fs.codigo_dane = fc.codigo_dane 
            AND fs.fecha_hecho::date = fc.fecha::date
        WHERE {where_sql}
        GROUP BY 
            CASE 
                WHEN fc.precipitacion_mm = 0 THEN '0 mm (Seco)'
                WHEN fc.precipitacion_mm < 2 THEN '0.1-2 mm (Muy ligera)'
                WHEN fc.precipitacion_mm < 5 THEN '2-5 mm (Ligera)'
                WHEN fc.precipitacion_mm < 10 THEN '5-10 mm (Moderada)'
                WHEN fc.precipitacion_mm < 20 THEN '10-20 mm (Fuerte)'
                ELSE '20+ mm (Muy fuerte)'
            END
        ORDER BY total_eventos DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    total_eventos = sum(r[1] for r in results)
    
    return {
        "descripcion": "Distribución de eventos por nivel de precipitación",
        "filtros": {
            "municipio": municipio,
            "categoria": categoria
        },
        "total_eventos_analizados": total_eventos,
        "distribucion": [
            {
                "rango": r[0],
                "total_eventos": r[1],
                "porcentaje": round(r[1] / total_eventos * 100, 2) if total_eventos > 0 else 0,
                "precipitacion_minima": float(r[2]) if r[2] else 0,
                "precipitacion_maxima": float(r[3]) if r[3] else 0,
                "precipitacion_promedio": float(r[4]) if r[4] else 0
            }
            for r in results
        ]
    }


def obtener_eventos_por_temperatura(
    db: Session,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Nota: La tabla fact_clima solo tiene precipitacion_mm.
    Esta función devuelve información sobre precipitación.
    """
    return obtener_eventos_por_precipitacion(db, municipio, categoria)


def obtener_resumen_climatico(
    db: Session,
    municipio: str = None
) -> dict:
    """
    Obtiene un resumen de los datos climáticos disponibles.
    """
    where_clauses = ["precipitacion_mm IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            COUNT(*) as total_registros,
            MIN(fecha) as fecha_inicio,
            MAX(fecha) as fecha_fin,
            COUNT(DISTINCT codigo_dane) as municipios_con_datos,
            ROUND(AVG(precipitacion_mm)::numeric, 2) as promedio_precipitacion,
            MAX(precipitacion_mm) as max_precipitacion,
            COUNT(CASE WHEN precipitacion_mm = 0 THEN 1 END) as dias_secos,
            COUNT(CASE WHEN precipitacion_mm > 0 THEN 1 END) as dias_con_lluvia
        FROM fact_clima
        WHERE {where_sql}
    """)
    
    result = db.execute(query, params).fetchone()
    
    # Días con más eventos
    query_dias_extremos = text(f"""
        WITH dias_eventos AS (
            SELECT 
                fc.fecha,
                fc.precipitacion_mm,
                COUNT(fs.id_evento) as eventos
            FROM fact_clima fc
            LEFT JOIN fact_seguridad fs ON fc.codigo_dane = fs.codigo_dane 
                AND fc.fecha = fs.fecha_hecho::date
            WHERE fc.precipitacion_mm IS NOT NULL
            {"AND fc.codigo_dane = :codigo_dane" if municipio and codigo_dane else ""}
            GROUP BY fc.fecha, fc.precipitacion_mm
        )
        SELECT 
            fecha,
            precipitacion_mm,
            eventos
        FROM dias_eventos
        WHERE eventos > 0
        ORDER BY eventos DESC
        LIMIT 10
    """)
    
    dias_extremos = db.execute(query_dias_extremos, params).fetchall()
    
    return {
        "descripcion": "Resumen de datos climáticos disponibles",
        "filtros": {
            "municipio": municipio
        },
        "estadisticas": {
            "total_registros": result[0],
            "periodo": f"{result[1]} a {result[2]}",
            "municipios_con_datos": result[3],
            "promedio_precipitacion_mm": float(result[4]) if result[4] else 0,
            "max_precipitacion_mm": float(result[5]) if result[5] else 0,
            "dias_secos": result[6],
            "dias_con_lluvia": result[7],
            "porcentaje_dias_secos": round(result[6] / result[0] * 100, 2) if result[0] > 0 else 0
        },
        "dias_con_mas_eventos": [
            {
                "fecha": str(r[0]),
                "precipitacion_mm": float(r[1]) if r[1] else 0,
                "total_eventos": r[2]
            }
            for r in dias_extremos
        ]
    }


def obtener_tendencia_mensual_clima(
    db: Session,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Analiza la tendencia mensual de precipitación vs eventos.
    """
    where_clauses = ["fc.precipitacion_mm IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("fc.codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    categoria_filter = ""
    if categoria:
        categoria_filter = "AND UPPER(fs.categoria_delito) = UPPER(:categoria)"
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        WITH datos_mensuales AS (
            SELECT 
                EXTRACT(MONTH FROM fc.fecha) as mes,
                fc.precipitacion_mm,
                (SELECT COUNT(*) FROM fact_seguridad fs 
                 WHERE fs.codigo_dane = fc.codigo_dane 
                 AND fs.fecha_hecho::date = fc.fecha::date
                 {categoria_filter}) as eventos
            FROM fact_clima fc
            WHERE {where_sql}
        )
        SELECT 
            mes,
            COUNT(*) as dias,
            SUM(eventos) as total_eventos,
            ROUND(AVG(precipitacion_mm)::numeric, 2) as promedio_precipitacion,
            ROUND(AVG(eventos)::numeric, 2) as promedio_eventos_dia
        FROM datos_mensuales
        GROUP BY mes
        ORDER BY mes
    """)
    
    results = db.execute(query, params).fetchall()
    
    nombres_meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    return {
        "descripcion": "Tendencia mensual de precipitación vs eventos",
        "filtros": {
            "municipio": municipio,
            "categoria": categoria
        },
        "datos_mensuales": [
            {
                "mes": int(r[0]),
                "nombre_mes": nombres_meses.get(int(r[0]), str(r[0])),
                "dias_analizados": r[1],
                "total_eventos": r[2],
                "promedio_precipitacion_mm": float(r[3]) if r[3] else 0,
                "promedio_eventos_dia": float(r[4]) if r[4] else 0
            }
            for r in results
        ]
    }
