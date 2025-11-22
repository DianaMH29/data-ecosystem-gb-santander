"""
Módulo de Consultas Geográficas del Chatbot
Consultas por municipio, rankings, comparaciones entre municipios
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from .chatbot_base import resolver_municipio, obtener_nombre_municipio


def obtener_datos_municipio(
    db: Session, 
    municipio: str,
    anio: int = None,
    categoria: str = None
) -> dict:
    """
    Obtiene estadísticas detalladas de un municipio específico.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    if not codigo_dane:
        return {"error": f"No se encontró el municipio: {municipio}"}
    
    nombre_municipio = obtener_nombre_municipio(db, codigo_dane)
    
    # Construir query dinámico
    where_clauses = ["codigo_dane = :codigo_dane"]
    params = {"codigo_dane": codigo_dane}
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    # Estadísticas generales
    query = text(f"""
        SELECT 
            COUNT(*) as total_eventos,
            COUNT(DISTINCT categoria_delito) as categorias_afectadas,
            MIN(fecha_hecho) as primer_evento,
            MAX(fecha_hecho) as ultimo_evento
        FROM fact_seguridad
        WHERE {where_sql}
    """)
    
    stats = db.execute(query, params).fetchone()
    
    # Distribución por categoría
    query_categorias = text(f"""
        SELECT 
            categoria_delito,
            COUNT(*) as cantidad
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY categoria_delito
        ORDER BY cantidad DESC
    """)
    
    categorias = db.execute(query_categorias, params).fetchall()
    
    # Distribución por año (si no hay filtro de año)
    tendencia = []
    if not anio:
        query_tendencia = text(f"""
            SELECT 
                EXTRACT(YEAR FROM fecha_hecho)::int as anio,
                COUNT(*) as cantidad
            FROM fact_seguridad
            WHERE {where_sql}
            GROUP BY anio
            ORDER BY anio
        """)
        tendencia = db.execute(query_tendencia, params).fetchall()
    
    return {
        "municipio": nombre_municipio,
        "codigo_dane": codigo_dane,
        "filtros_aplicados": {
            "anio": anio,
            "categoria": categoria
        },
        "estadisticas": {
            "total_eventos": stats.total_eventos,
            "categorias_afectadas": stats.categorias_afectadas,
            "periodo": f"{stats.primer_evento} a {stats.ultimo_evento}" if stats.primer_evento else "Sin datos"
        },
        "distribucion_categorias": [
            {"categoria": r[0], "cantidad": r[1]} for r in categorias
        ],
        "tendencia_anual": [
            {"anio": r[0], "cantidad": r[1]} for r in tendencia
        ] if tendencia else None
    }


def obtener_ranking_municipios(
    db: Session,
    categoria: str = None,
    anio: int = None,
    limite: int = 10,
    orden: str = "desc"
) -> dict:
    """
    Obtiene el ranking de municipios por cantidad de eventos (absoluto).
    """
    where_clauses = ["1=1"]
    params = {"limite": limite}
    
    if categoria:
        where_clauses.append("UPPER(fs.categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fs.fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    order_dir = "DESC" if orden.lower() == "desc" else "ASC"
    
    query = text(f"""
        SELECT 
            mm.nombre_municipio,
            mm.codigo_dane,
            COUNT(*) as total_eventos
        FROM fact_seguridad fs
        JOIN master_municipios mm ON fs.codigo_dane = mm.codigo_dane
        WHERE {where_sql}
        GROUP BY mm.nombre_municipio, mm.codigo_dane
        ORDER BY total_eventos {order_dir}
        LIMIT :limite
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "tipo_ranking": "absoluto",
        "orden": "mayor a menor" if orden.lower() == "desc" else "menor a mayor",
        "filtros": {
            "categoria": categoria,
            "anio": anio
        },
        "ranking": [
            {
                "posicion": i + 1,
                "municipio": r[0],
                "codigo_dane": r[1],
                "total_eventos": r[2]
            } for i, r in enumerate(results)
        ]
    }


def obtener_ranking_por_tasa(
    db: Session,
    categoria: str = None,
    anio: int = None,
    limite: int = 10,
    orden: str = "desc"
) -> dict:
    """
    Obtiene el ranking de municipios por tasa de criminalidad 
    (eventos por cada 100,000 habitantes).
    """
    where_clauses = ["1=1"]
    params = {"limite": limite}
    
    if categoria:
        where_clauses.append("UPPER(fs.categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fs.fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    order_dir = "DESC" if orden.lower() == "desc" else "ASC"
    
    query = text(f"""
        SELECT 
            mm.nombre_municipio,
            mm.codigo_dane,
            COUNT(*) as total_eventos,
            md.poblacion_total,
            CASE 
                WHEN md.poblacion_total > 0 
                THEN ROUND((COUNT(*)::numeric / md.poblacion_total * 100000), 2)
                ELSE 0 
            END as tasa_por_100k
        FROM fact_seguridad fs
        JOIN master_municipios mm ON fs.codigo_dane = mm.codigo_dane
        LEFT JOIN master_demografia md ON fs.codigo_dane = md.codigo_dane
        WHERE {where_sql}
        GROUP BY mm.nombre_municipio, mm.codigo_dane, md.poblacion_total
        HAVING md.poblacion_total > 0
        ORDER BY tasa_por_100k {order_dir}
        LIMIT :limite
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "tipo_ranking": "por_tasa",
        "descripcion": "Eventos por cada 100,000 habitantes",
        "orden": "mayor a menor" if orden.lower() == "desc" else "menor a mayor",
        "filtros": {
            "categoria": categoria,
            "anio": anio
        },
        "ranking": [
            {
                "posicion": i + 1,
                "municipio": r[0],
                "codigo_dane": r[1],
                "total_eventos": r[2],
                "poblacion": r[3],
                "tasa_por_100k": float(r[4]) if r[4] else 0
            } for i, r in enumerate(results)
        ]
    }


def comparar_municipios(
    db: Session,
    municipios: list[str],
    anio: int = None,
    categoria: str = None
) -> dict:
    """
    Compara estadísticas entre múltiples municipios.
    """
    resultados = []
    
    for municipio in municipios:
        codigo_dane = resolver_municipio(db, municipio)
        if not codigo_dane:
            resultados.append({
                "municipio": municipio,
                "error": "No encontrado"
            })
            continue
        
        nombre = obtener_nombre_municipio(db, codigo_dane)
        
        where_clauses = ["fs.codigo_dane = :codigo_dane"]
        params = {"codigo_dane": codigo_dane}
        
        if anio:
            where_clauses.append("EXTRACT(YEAR FROM fs.fecha_hecho) = :anio")
            params["anio"] = anio
        
        if categoria:
            where_clauses.append("UPPER(fs.categoria_delito) = UPPER(:categoria)")
            params["categoria"] = categoria
        
        where_sql = " AND ".join(where_clauses)
        
        query = text(f"""
            SELECT 
                COUNT(*) as total_eventos,
                md.poblacion_total,
                CASE 
                    WHEN md.poblacion_total > 0 
                    THEN ROUND((COUNT(*)::numeric / md.poblacion_total * 100000), 2)
                    ELSE 0 
                END as tasa_por_100k
            FROM fact_seguridad fs
            LEFT JOIN master_demografia md ON fs.codigo_dane = md.codigo_dane
            WHERE {where_sql}
            GROUP BY md.poblacion_total
        """)
        
        stats = db.execute(query, params).fetchone()
        
        # Distribución por categoría
        query_cat = text(f"""
            SELECT categoria_delito, COUNT(*) as cantidad
            FROM fact_seguridad fs
            WHERE {where_sql}
            GROUP BY categoria_delito
            ORDER BY cantidad DESC
        """)
        categorias = db.execute(query_cat, params).fetchall()
        
        resultados.append({
            "municipio": nombre,
            "codigo_dane": codigo_dane,
            "total_eventos": stats.total_eventos if stats else 0,
            "poblacion": stats.poblacion_total if stats else None,
            "tasa_por_100k": float(stats.tasa_por_100k) if stats and stats.tasa_por_100k else 0,
            "distribucion": {r[0]: r[1] for r in categorias}
        })
    
    return {
        "comparacion": resultados,
        "filtros": {
            "anio": anio,
            "categoria": categoria
        }
    }


def obtener_municipios_cercanos(
    db: Session,
    municipio: str,
    radio_km: float = 50
) -> dict:
    """
    Obtiene municipios cercanos a uno dado y compara sus estadísticas.
    Usa PostGIS para cálculo de distancias.
    """
    codigo_dane = resolver_municipio(db, municipio)
    
    if not codigo_dane:
        return {"error": f"No se encontró el municipio: {municipio}"}
    
    nombre = obtener_nombre_municipio(db, codigo_dane)
    
    query = text("""
        WITH municipio_origen AS (
            SELECT geom FROM master_municipios WHERE codigo_dane = :codigo_dane
        )
        SELECT 
            mm.nombre_municipio,
            mm.codigo_dane,
            ST_Distance(mm.geom::geography, mo.geom::geography) / 1000 as distancia_km,
            (SELECT COUNT(*) FROM fact_seguridad WHERE codigo_dane = mm.codigo_dane) as total_eventos
        FROM master_municipios mm, municipio_origen mo
        WHERE mm.codigo_dane != :codigo_dane
        AND ST_DWithin(mm.geom::geography, mo.geom::geography, :radio_metros)
        ORDER BY distancia_km
    """)
    
    results = db.execute(query, {
        "codigo_dane": codigo_dane,
        "radio_metros": radio_km * 1000
    }).fetchall()
    
    return {
        "municipio_origen": nombre,
        "radio_busqueda_km": radio_km,
        "municipios_cercanos": [
            {
                "municipio": r[0],
                "codigo_dane": r[1],
                "distancia_km": round(r[2], 2),
                "total_eventos": r[3]
            } for r in results
        ]
    }
