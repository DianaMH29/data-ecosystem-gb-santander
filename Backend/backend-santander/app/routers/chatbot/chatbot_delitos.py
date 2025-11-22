"""
Módulo de Consultas de Delitos del Chatbot
Consultas por categoría de delito, modalidad específica, arma/medio utilizado, clase de sitio
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from .chatbot_base import resolver_municipio, obtener_nombre_municipio


def obtener_datos_por_categoria(
    db: Session,
    categoria: str,
    municipio: str = None,
    anio: int = None
) -> dict:
    """
    Obtiene estadísticas detalladas de una categoría de delito específica.
    """
    where_clauses = ["UPPER(categoria_delito) = UPPER(:categoria)"]
    params = {"categoria": categoria}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    
    # Estadísticas generales
    query_stats = text(f"""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT codigo_dane) as municipios_afectados,
            MIN(fecha_hecho) as primer_evento,
            MAX(fecha_hecho) as ultimo_evento
        FROM fact_seguridad
        WHERE {where_sql}
    """)
    
    stats = db.execute(query_stats, params).fetchone()
    
    # Modalidades más comunes
    query_modalidad = text(f"""
        SELECT modalidad_especifica, COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql} AND modalidad_especifica IS NOT NULL
        GROUP BY modalidad_especifica
        ORDER BY total DESC
        LIMIT 10
    """)
    
    modalidades = db.execute(query_modalidad, params).fetchall()
    
    # Armas más usadas
    query_armas = text(f"""
        SELECT arma_medio, COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql} AND arma_medio IS NOT NULL
        GROUP BY arma_medio
        ORDER BY total DESC
        LIMIT 10
    """)
    
    armas = db.execute(query_armas, params).fetchall()
    
    # Tendencia anual
    query_tendencia = text(f"""
        SELECT EXTRACT(YEAR FROM fecha_hecho)::int as anio, COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY anio
        ORDER BY anio
    """)
    
    tendencia = db.execute(query_tendencia, params).fetchall()
    
    return {
        "categoria": categoria,
        "filtros": {
            "municipio": municipio,
            "anio": anio
        },
        "estadisticas": {
            "total_eventos": stats.total,
            "municipios_afectados": stats.municipios_afectados,
            "periodo": f"{stats.primer_evento} a {stats.ultimo_evento}" if stats.primer_evento else "Sin datos"
        },
        "modalidades_frecuentes": [
            {"modalidad": r[0], "total": r[1]} for r in modalidades
        ],
        "armas_medios_frecuentes": [
            {"arma_medio": r[0], "total": r[1]} for r in armas
        ],
        "tendencia_anual": [
            {"anio": r[0], "total": r[1]} for r in tendencia
        ]
    }


def obtener_datos_por_modalidad(
    db: Session,
    modalidad: str,
    municipio: str = None,
    anio: int = None
) -> dict:
    """
    Obtiene estadísticas de una modalidad específica de delito.
    """
    where_clauses = ["modalidad_especifica ILIKE :modalidad"]
    params = {"modalidad": f"%{modalidad}%"}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    
    # Estadísticas
    query = text(f"""
        SELECT 
            modalidad_especifica,
            categoria_delito,
            COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY modalidad_especifica, categoria_delito
        ORDER BY total DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Municipios más afectados
    query_mun = text(f"""
        SELECT mm.nombre_municipio, COUNT(*) as total
        FROM fact_seguridad fs
        JOIN master_municipios mm ON fs.codigo_dane = mm.codigo_dane
        WHERE {where_sql.replace('codigo_dane', 'fs.codigo_dane')}
        GROUP BY mm.nombre_municipio
        ORDER BY total DESC
        LIMIT 10
    """)
    
    municipios = db.execute(query_mun, params).fetchall()
    
    return {
        "modalidad_buscada": modalidad,
        "filtros": {
            "municipio": municipio,
            "anio": anio
        },
        "resultados": [
            {
                "modalidad": r[0],
                "categoria": r[1],
                "total": r[2]
            } for r in results
        ],
        "municipios_afectados": [
            {"municipio": r[0], "total": r[1]} for r in municipios
        ],
        "total_general": sum(r[2] for r in results)
    }


def obtener_datos_por_arma(
    db: Session,
    arma: str,
    municipio: str = None,
    anio: int = None
) -> dict:
    """
    Obtiene estadísticas de delitos por arma/medio utilizado.
    """
    where_clauses = ["arma_medio ILIKE :arma"]
    params = {"arma": f"%{arma}%"}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    
    # Por categoría de delito
    query_cat = text(f"""
        SELECT categoria_delito, COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY categoria_delito
        ORDER BY total DESC
    """)
    
    categorias = db.execute(query_cat, params).fetchall()
    
    # Tendencia
    query_tendencia = text(f"""
        SELECT EXTRACT(YEAR FROM fecha_hecho)::int as anio, COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY anio
        ORDER BY anio
    """)
    
    tendencia = db.execute(query_tendencia, params).fetchall()
    
    # Perfil víctimas
    query_perfil = text(f"""
        SELECT genero, grupo_etario, COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql} AND genero IS NOT NULL
        GROUP BY genero, grupo_etario
        ORDER BY total DESC
        LIMIT 5
    """)
    
    perfil = db.execute(query_perfil, params).fetchall()
    
    return {
        "arma_buscada": arma,
        "filtros": {
            "municipio": municipio,
            "anio": anio
        },
        "por_categoria": [
            {"categoria": r[0], "total": r[1]} for r in categorias
        ],
        "tendencia_anual": [
            {"anio": r[0], "total": r[1]} for r in tendencia
        ],
        "perfil_victimas": [
            {"genero": r[0], "grupo_etario": r[1], "total": r[2]} for r in perfil
        ],
        "total_general": sum(r[1] for r in categorias)
    }


def obtener_datos_por_sitio(
    db: Session,
    clase_sitio: str,
    municipio: str = None,
    anio: int = None
) -> dict:
    """
    Obtiene estadísticas de delitos por clase de sitio.
    """
    where_clauses = ["clase_sitio ILIKE :sitio"]
    params = {"sitio": f"%{clase_sitio}%"}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    
    # Por categoría
    query = text(f"""
        SELECT 
            clase_sitio,
            categoria_delito,
            COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY clase_sitio, categoria_delito
        ORDER BY total DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Horarios si aplica
    query_hora = text(f"""
        SELECT 
            EXTRACT(HOUR FROM fecha_hecho)::int as hora,
            COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY hora
        ORDER BY total DESC
        LIMIT 5
    """)
    
    horas = db.execute(query_hora, params).fetchall()
    
    return {
        "sitio_buscado": clase_sitio,
        "filtros": {
            "municipio": municipio,
            "anio": anio
        },
        "resultados": [
            {
                "clase_sitio": r[0],
                "categoria": r[1],
                "total": r[2]
            } for r in results
        ],
        "horas_pico": [
            {"hora": r[0], "total": r[1]} for r in horas
        ],
        "total_general": sum(r[2] for r in results)
    }


def obtener_ranking_categorias(
    db: Session,
    municipio: str = None,
    anio: int = None
) -> dict:
    """
    Obtiene el ranking de categorías de delito.
    """
    where_clauses = ["categoria_delito IS NOT NULL"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            categoria_delito,
            COUNT(*) as total,
            ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY categoria_delito
        ORDER BY total DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "filtros": {
            "municipio": municipio,
            "anio": anio
        },
        "ranking": [
            {
                "posicion": i + 1,
                "categoria": r[0],
                "total": r[1],
                "porcentaje": float(r[2])
            } for i, r in enumerate(results)
        ],
        "total_general": sum(r[1] for r in results)
    }


def obtener_ranking_modalidades(
    db: Session,
    categoria: str = None,
    municipio: str = None,
    anio: int = None,
    limite: int = 20
) -> dict:
    """
    Obtiene el ranking de modalidades específicas.
    """
    where_clauses = ["modalidad_especifica IS NOT NULL"]
    params = {"limite": limite}
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            modalidad_especifica,
            COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY modalidad_especifica
        ORDER BY total DESC
        LIMIT :limite
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "filtros": {
            "categoria": categoria,
            "municipio": municipio,
            "anio": anio
        },
        "ranking": [
            {
                "posicion": i + 1,
                "modalidad": r[0],
                "total": r[1]
            } for i, r in enumerate(results)
        ]
    }


def obtener_ranking_armas(
    db: Session,
    categoria: str = None,
    municipio: str = None,
    anio: int = None,
    limite: int = 20
) -> dict:
    """
    Obtiene el ranking de armas/medios utilizados.
    """
    where_clauses = ["arma_medio IS NOT NULL"]
    params = {"limite": limite}
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            arma_medio,
            COUNT(*) as total,
            ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY arma_medio
        ORDER BY total DESC
        LIMIT :limite
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "filtros": {
            "categoria": categoria,
            "municipio": municipio,
            "anio": anio
        },
        "ranking": [
            {
                "posicion": i + 1,
                "arma_medio": r[0],
                "total": r[1],
                "porcentaje": float(r[2])
            } for i, r in enumerate(results)
        ]
    }


def obtener_ranking_sitios(
    db: Session,
    categoria: str = None,
    municipio: str = None,
    anio: int = None,
    limite: int = 20
) -> dict:
    """
    Obtiene el ranking de clases de sitio.
    """
    where_clauses = ["clase_sitio IS NOT NULL"]
    params = {"limite": limite}
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            clase_sitio,
            COUNT(*) as total,
            ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY clase_sitio
        ORDER BY total DESC
        LIMIT :limite
    """)
    
    results = db.execute(query, params).fetchall()
    
    return {
        "filtros": {
            "categoria": categoria,
            "municipio": municipio,
            "anio": anio
        },
        "ranking": [
            {
                "posicion": i + 1,
                "clase_sitio": r[0],
                "total": r[1],
                "porcentaje": float(r[2])
            } for i, r in enumerate(results)
        ]
    }


def comparar_categorias(
    db: Session,
    categorias: list[str],
    municipio: str = None,
    anio: int = None
) -> dict:
    """
    Compara múltiples categorías de delito.
    """
    resultados = []
    
    for categoria in categorias:
        where_clauses = ["UPPER(categoria_delito) = UPPER(:categoria)"]
        params = {"categoria": categoria}
        
        if municipio:
            codigo_dane = resolver_municipio(db, municipio)
            if codigo_dane:
                where_clauses.append("codigo_dane = :codigo_dane")
                params["codigo_dane"] = codigo_dane
        
        if anio:
            where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
            params["anio"] = anio
        
        where_sql = " AND ".join(where_clauses)
        
        query = text(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE UPPER(genero) = 'FEMENINO') as femenino,
                COUNT(*) FILTER (WHERE UPPER(genero) = 'MASCULINO') as masculino,
                COUNT(*) FILTER (WHERE UPPER(zona) = 'URBANA') as urbano
            FROM fact_seguridad
            WHERE {where_sql}
        """)
        
        stats = db.execute(query, params).fetchone()
        
        resultados.append({
            "categoria": categoria,
            "total": stats.total,
            "porcentaje_femenino": round(stats.femenino * 100 / stats.total, 2) if stats.total > 0 else 0,
            "porcentaje_masculino": round(stats.masculino * 100 / stats.total, 2) if stats.total > 0 else 0,
            "porcentaje_urbano": round(stats.urbano * 100 / stats.total, 2) if stats.total > 0 else 0
        })
    
    return {
        "filtros": {
            "municipio": municipio,
            "anio": anio
        },
        "comparativa": resultados
    }
