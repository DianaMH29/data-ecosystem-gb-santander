"""
Módulo de Consultas Demográficas del Chatbot
Consultas por género, grupo etario, zona_hecho (urbana/rural)
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from .chatbot_base import resolver_municipio, obtener_nombre_municipio


def obtener_distribucion_genero(
    db: Session,
    municipio: str = None,
    anio: int = None,
    categoria: str = None
) -> dict:
    """
    Obtiene la distribución de eventos por género de la víctima.
    """
    where_clauses = ["genero IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            genero,
            COUNT(*) as total,
            ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY genero
        ORDER BY total DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "filtros": {
            "municipio": municipio,
            "anio": anio,
            "categoria": categoria
        },
        "distribucion": [
            {
                "genero": r[0],
                "total": r[1],
                "porcentaje": float(r[2])
            } for r in results
        ],
        "total_general": sum(r[1] for r in results),
        "genero_mas_afectado": results[0][0] if results else None
    }


def obtener_distribucion_grupo_etario(
    db: Session,
    municipio: str = None,
    anio: int = None,
    categoria: str = None,
    genero: str = None
) -> dict:
    """
    Obtiene la distribución de eventos por grupo etario.
    """
    where_clauses = ["grupo_etario IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    if genero:
        where_clauses.append("UPPER(genero) = UPPER(:genero)")
        params["genero"] = genero
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            grupo_etario,
            COUNT(*) as total,
            ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY grupo_etario
        ORDER BY total DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "filtros": {
            "municipio": municipio,
            "anio": anio,
            "categoria": categoria,
            "genero": genero
        },
        "distribucion": [
            {
                "grupo_etario": r[0],
                "total": r[1],
                "porcentaje": float(r[2])
            } for r in results
        ],
        "total_general": sum(r[1] for r in results),
        "grupo_mas_afectado": results[0][0] if results else None
    }


def obtener_distribucion_zona(
    db: Session,
    municipio: str = None,
    anio: int = None,
    categoria: str = None
) -> dict:
    """
    Obtiene la distribución de eventos por zona_hecho (urbana/rural).
    """
    where_clauses = ["zona_hecho IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            zona_hecho,
            COUNT(*) as total,
            ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY zona_hecho
        ORDER BY total DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "filtros": {
            "municipio": municipio,
            "anio": anio,
            "categoria": categoria
        },
        "distribucion": [
            {
                "zona_hecho": r[0],
                "total": r[1],
                "porcentaje": float(r[2])
            } for r in results
        ],
        "total_general": sum(r[1] for r in results)
    }


def obtener_perfil_victima(
    db: Session,
    municipio: str = None,
    anio: int = None,
    categoria: str = None
) -> dict:
    """
    Obtiene el perfil demográfico completo de las víctimas.
    Combina género, grupo etario y zona_hecho.
    """
    where_clauses = ["1=1"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    # Combinación género + grupo etario
    query_perfil = text(f"""
        SELECT 
            genero,
            grupo_etario,
            COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        AND genero IS NOT NULL
        AND grupo_etario IS NOT NULL
        GROUP BY genero, grupo_etario
        ORDER BY total DESC
        LIMIT 10
    """)
    
    perfiles = db.execute(query_perfil, params).fetchall()
    
    # Estadísticas generales
    query_stats = text(f"""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE UPPER(genero) = 'MASCULINO') as masculino,
            COUNT(*) FILTER (WHERE UPPER(genero) = 'FEMENINO') as femenino,
            COUNT(*) FILTER (WHERE UPPER(zona_hecho) = 'URBANA') as urbano,
            COUNT(*) FILTER (WHERE UPPER(zona_hecho) = 'RURAL') as rural
        FROM fact_seguridad
        WHERE {where_sql}
    """)
    
    stats = db.execute(query_stats, params).fetchone()
    
    return {
        "filtros": {
            "municipio": municipio,
            "anio": anio,
            "categoria": categoria
        },
        "perfiles_mas_afectados": [
            {
                "genero": r[0],
                "grupo_etario": r[1],
                "total": r[2]
            } for r in perfiles
        ],
        "resumen": {
            "total_eventos": stats.total,
            "distribucion_genero": {
                "masculino": stats.masculino,
                "femenino": stats.femenino,
                "porcentaje_masculino": round(stats.masculino * 100 / stats.total, 2) if stats.total > 0 else 0,
                "porcentaje_femenino": round(stats.femenino * 100 / stats.total, 2) if stats.total > 0 else 0
            },
            "distribucion_zona": {
                "urbano": stats.urbano,
                "rural": stats.rural,
                "porcentaje_urbano": round(stats.urbano * 100 / stats.total, 2) if stats.total > 0 else 0,
                "porcentaje_rural": round(stats.rural * 100 / stats.total, 2) if stats.total > 0 else 0
            }
        }
    }


def obtener_vulnerabilidad_por_delito(
    db: Session,
    anio: int = None,
    municipio: str = None
) -> dict:
    """
    Analiza qué grupos demográficos son más vulnerables a cada tipo de delito.
    """
    where_clauses = ["genero IS NOT NULL", "grupo_etario IS NOT NULL"]
    params = {}
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            categoria_delito,
            genero,
            grupo_etario,
            COUNT(*) as total,
            ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER(PARTITION BY categoria_delito), 2) as porcentaje
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY categoria_delito, genero, grupo_etario
        ORDER BY categoria_delito, total DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Organizar por categoría
    por_categoria = {}
    for r in results:
        cat = r[0]
        if cat not in por_categoria:
            por_categoria[cat] = []
        por_categoria[cat].append({
            "genero": r[1],
            "grupo_etario": r[2],
            "total": r[3],
            "porcentaje": float(r[4])
        })
    
    # Identificar grupo más vulnerable por categoría
    vulnerabilidad = {}
    for cat, datos in por_categoria.items():
        if datos:
            mas_vulnerable = datos[0]
            vulnerabilidad[cat] = {
                "grupo_mas_vulnerable": f"{mas_vulnerable['genero']} - {mas_vulnerable['grupo_etario']}",
                "porcentaje": mas_vulnerable["porcentaje"],
                "total": mas_vulnerable["total"]
            }
    
    return {
        "filtros": {
            "anio": anio,
            "municipio": municipio
        },
        "detalle_por_categoria": por_categoria,
        "resumen_vulnerabilidad": vulnerabilidad
    }


def comparar_genero_por_anio(
    db: Session,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Compara la evolución de eventos por género a lo largo de los años.
    """
    where_clauses = ["genero IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            EXTRACT(YEAR FROM fecha_hecho)::int as anio,
            genero,
            COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY anio, genero
        ORDER BY anio, genero
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Organizar por año
    por_anio = {}
    for r in results:
        anio = r[0]
        if anio not in por_anio:
            por_anio[anio] = {}
        por_anio[anio][r[1]] = r[2]
    
    # Convertir a lista
    tendencia = []
    for anio, generos in sorted(por_anio.items()):
        total = sum(generos.values())
        tendencia.append({
            "anio": anio,
            "masculino": generos.get("MASCULINO", 0),
            "femenino": generos.get("FEMENINO", 0),
            "total": total,
            "porcentaje_femenino": round(generos.get("FEMENINO", 0) * 100 / total, 2) if total > 0 else 0
        })
    
    return {
        "filtros": {
            "municipio": municipio,
            "categoria": categoria
        },
        "tendencia": tendencia
    }


def obtener_ranking_municipios_por_genero(
    db: Session,
    genero: str,
    anio: int = None,
    categoria: str = None,
    limite: int = 10
) -> dict:
    """
    Obtiene ranking de municipios para un género específico.
    """
    where_clauses = ["UPPER(fs.genero) = UPPER(:genero)"]
    params = {"genero": genero, "limite": limite}
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fs.fecha_hecho) = :anio")
        params["anio"] = anio
    
    if categoria:
        where_clauses.append("UPPER(fs.categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            mm.nombre_municipio,
            COUNT(*) as total
        FROM fact_seguridad fs
        JOIN master_municipios mm ON fs.codigo_dane = mm.codigo_dane
        WHERE {where_sql}
        GROUP BY mm.nombre_municipio
        ORDER BY total DESC
        LIMIT :limite
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "genero_consultado": genero,
        "filtros": {
            "anio": anio,
            "categoria": categoria
        },
        "ranking": [
            {
                "posicion": i + 1,
                "municipio": r[0],
                "total": r[1]
            } for i, r in enumerate(results)
        ]
    }
