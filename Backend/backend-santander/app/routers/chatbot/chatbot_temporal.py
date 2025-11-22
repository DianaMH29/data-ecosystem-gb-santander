"""
Módulo de Consultas Temporales del Chatbot
Consultas por año, mes, día de semana, rangos de fechas, tendencias
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from .chatbot_base import resolver_municipio, obtener_nombre_municipio


# Mapeo de nombres de días y meses en español
DIAS_SEMANA = {
    0: "Domingo",
    1: "Lunes", 
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado"
}

MESES = {
    1: "Enero",
    2: "Febrero", 
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}


def obtener_tendencia_anual(
    db: Session,
    municipio: str = None,
    categoria: str = None,
    anio_inicio: int = None,
    anio_fin: int = None
) -> dict:
    """
    Obtiene la tendencia anual de eventos.
    """
    where_clauses = ["1=1"]
    params = {}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    if anio_inicio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) >= :anio_inicio")
        params["anio_inicio"] = anio_inicio
    
    if anio_fin:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) <= :anio_fin")
        params["anio_fin"] = anio_fin
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT 
            EXTRACT(YEAR FROM fecha_hecho)::int as anio,
            COUNT(*) as total_eventos
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY anio
        ORDER BY anio
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Calcular variación porcentual
    tendencia = []
    for i, r in enumerate(results):
        variacion = None
        if i > 0 and results[i-1][1] > 0:
            variacion = round(((r[1] - results[i-1][1]) / results[i-1][1]) * 100, 2)
        
        tendencia.append({
            "anio": r[0],
            "total_eventos": r[1],
            "variacion_porcentual": variacion
        })
    
    return {
        "filtros": {
            "municipio": municipio,
            "categoria": categoria,
            "periodo": f"{anio_inicio or 'inicio'} - {anio_fin or 'actual'}"
        },
        "tendencia": tendencia,
        "resumen": {
            "total_general": sum(r[1] for r in results),
            "promedio_anual": round(sum(r[1] for r in results) / len(results), 2) if results else 0,
            "anio_max": max(results, key=lambda x: x[1])[0] if results else None,
            "anio_min": min(results, key=lambda x: x[1])[0] if results else None
        }
    }


def obtener_datos_por_mes(
    db: Session,
    anio: int = None,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Obtiene la distribución de eventos por mes.
    """
    where_clauses = ["1=1"]
    params = {}
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
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
            EXTRACT(MONTH FROM fecha_hecho)::int as mes,
            COUNT(*) as total_eventos
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY mes
        ORDER BY mes
    """)
    
    results = db.execute(query, params).fetchall()
    
    distribucion = []
    for r in results:
        distribucion.append({
            "mes": r[0],
            "nombre_mes": MESES.get(r[0], str(r[0])),
            "total_eventos": r[1]
        })
    
    return {
        "filtros": {
            "anio": anio,
            "municipio": municipio,
            "categoria": categoria
        },
        "distribucion_mensual": distribucion,
        "mes_mas_critico": max(distribucion, key=lambda x: x["total_eventos"]) if distribucion else None,
        "mes_menos_critico": min(distribucion, key=lambda x: x["total_eventos"]) if distribucion else None
    }


def obtener_datos_por_dia_semana(
    db: Session,
    anio: int = None,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Obtiene la distribución de eventos por día de la semana.
    """
    where_clauses = ["1=1"]
    params = {}
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    # EXTRACT(DOW) en PostgreSQL: 0=Domingo, 1=Lunes, ..., 6=Sábado
    query = text(f"""
        SELECT 
            EXTRACT(DOW FROM fecha_hecho)::int as dia_semana,
            COUNT(*) as total_eventos
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY dia_semana
        ORDER BY dia_semana
    """)
    
    results = db.execute(query, params).fetchall()
    
    distribucion = []
    for r in results:
        distribucion.append({
            "dia_semana": r[0],
            "nombre_dia": DIAS_SEMANA.get(r[0], str(r[0])),
            "total_eventos": r[1]
        })
    
    # Separar días laborables y fin de semana
    laborables = sum(d["total_eventos"] for d in distribucion if d["dia_semana"] in [1,2,3,4,5])
    fin_semana = sum(d["total_eventos"] for d in distribucion if d["dia_semana"] in [0,6])
    
    return {
        "filtros": {
            "anio": anio,
            "municipio": municipio,
            "categoria": categoria
        },
        "distribucion_semanal": distribucion,
        "dia_mas_critico": max(distribucion, key=lambda x: x["total_eventos"]) if distribucion else None,
        "dia_menos_critico": min(distribucion, key=lambda x: x["total_eventos"]) if distribucion else None,
        "comparacion": {
            "dias_laborables": laborables,
            "fin_de_semana": fin_semana,
            "promedio_laborables": round(laborables / 5, 2) if laborables else 0,
            "promedio_fin_semana": round(fin_semana / 2, 2) if fin_semana else 0
        }
    }


def obtener_datos_rango_fechas(
    db: Session,
    fecha_inicio: str,
    fecha_fin: str,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Obtiene estadísticas para un rango específico de fechas.
    Formato de fechas: YYYY-MM-DD
    """
    where_clauses = [
        "fecha_hecho >= :fecha_inicio",
        "fecha_hecho <= :fecha_fin"
    ]
    params = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    if categoria:
        where_clauses.append("UPPER(categoria_delito) = UPPER(:categoria)")
        params["categoria"] = categoria
    
    where_sql = " AND ".join(where_clauses)
    
    # Estadísticas generales
    query_stats = text(f"""
        SELECT 
            COUNT(*) as total_eventos,
            COUNT(DISTINCT codigo_dane) as municipios_afectados,
            COUNT(DISTINCT categoria_delito) as categorias
        FROM fact_seguridad
        WHERE {where_sql}
    """)
    
    stats = db.execute(query_stats, params).fetchone()
    
    # Distribución por categoría
    query_cat = text(f"""
        SELECT categoria_delito, COUNT(*) as cantidad
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY categoria_delito
        ORDER BY cantidad DESC
    """)
    
    categorias = db.execute(query_cat, params).fetchall()
    
    # Distribución diaria
    query_diario = text(f"""
        SELECT 
            fecha_hecho::date as fecha,
            COUNT(*) as total
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY fecha_hecho::date
        ORDER BY fecha
    """)
    
    diario = db.execute(query_diario, params).fetchall()
    
    return {
        "rango": {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        },
        "filtros": {
            "municipio": municipio,
            "categoria": categoria
        },
        "estadisticas": {
            "total_eventos": stats.total_eventos,
            "municipios_afectados": stats.municipios_afectados,
            "categorias_registradas": stats.categorias
        },
        "distribucion_categorias": [
            {"categoria": r[0], "cantidad": r[1]} for r in categorias
        ],
        "serie_diaria": [
            {"fecha": str(r[0]), "total": r[1]} for r in diario
        ]
    }


def obtener_datos_fecha_especifica(
    db: Session,
    fecha: str,
    municipio: str = None
) -> dict:
    """
    Obtiene todos los eventos de una fecha específica.
    Formato: YYYY-MM-DD
    """
    where_clauses = ["fecha_hecho::date = :fecha"]
    params = {"fecha": fecha}
    
    if municipio:
        codigo_dane = resolver_municipio(db, municipio)
        if codigo_dane:
            where_clauses.append("codigo_dane = :codigo_dane")
            params["codigo_dane"] = codigo_dane
    
    where_sql = " AND ".join(where_clauses)
    
    # Total y distribución
    query = text(f"""
        SELECT 
            COUNT(*) as total,
            categoria_delito,
            COUNT(*) as por_categoria
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY categoria_delito
        ORDER BY por_categoria DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Municipios afectados
    query_mun = text(f"""
        SELECT 
            mm.nombre_municipio,
            COUNT(*) as total
        FROM fact_seguridad fs
        JOIN master_municipios mm ON fs.codigo_dane = mm.codigo_dane
        WHERE {where_sql.replace('codigo_dane', 'fs.codigo_dane')}
        GROUP BY mm.nombre_municipio
        ORDER BY total DESC
        LIMIT 10
    """)
    
    municipios = db.execute(query_mun, params).fetchall()
    
    total = sum(r[2] for r in results) if results else 0
    
    return {
        "fecha": fecha,
        "filtros": {
            "municipio": municipio
        },
        "total_eventos": total,
        "distribucion_categorias": [
            {"categoria": r[1], "cantidad": r[2]} for r in results
        ],
        "municipios_mas_afectados": [
            {"municipio": r[0], "total": r[1]} for r in municipios
        ]
    }


def obtener_comparativa_periodos(
    db: Session,
    anio_1: int,
    anio_2: int,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Compara dos años o períodos.
    """
    resultados = {}
    
    for anio in [anio_1, anio_2]:
        where_clauses = ["EXTRACT(YEAR FROM fecha_hecho) = :anio"]
        params = {"anio": anio}
        
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
                COUNT(*) as total,
                COUNT(DISTINCT codigo_dane) as municipios
            FROM fact_seguridad
            WHERE {where_sql}
        """)
        
        stats = db.execute(query, params).fetchone()
        
        # Por categoría
        query_cat = text(f"""
            SELECT categoria_delito, COUNT(*) as cantidad
            FROM fact_seguridad
            WHERE {where_sql}
            GROUP BY categoria_delito
        """)
        
        categorias = db.execute(query_cat, params).fetchall()
        
        resultados[str(anio)] = {
            "total_eventos": stats.total,
            "municipios_afectados": stats.municipios,
            "por_categoria": {r[0]: r[1] for r in categorias}
        }
    
    # Calcular variación
    total_1 = resultados[str(anio_1)]["total_eventos"]
    total_2 = resultados[str(anio_2)]["total_eventos"]
    
    variacion = None
    if total_1 > 0:
        variacion = round(((total_2 - total_1) / total_1) * 100, 2)
    
    return {
        "comparativa": resultados,
        "analisis": {
            "variacion_porcentual": variacion,
            "diferencia_absoluta": total_2 - total_1,
            "tendencia": "aumento" if total_2 > total_1 else "disminución" if total_2 < total_1 else "estable"
        },
        "filtros": {
            "municipio": municipio,
            "categoria": categoria
        }
    }


def obtener_horario_eventos(
    db: Session,
    anio: int = None,
    municipio: str = None,
    categoria: str = None
) -> dict:
    """
    Obtiene distribución de eventos por hora del día (si la data tiene hora).
    Nota: Depende de que fecha_hecho tenga componente de hora.
    """
    where_clauses = ["1=1"]
    params = {}
    
    if anio:
        where_clauses.append("EXTRACT(YEAR FROM fecha_hecho) = :anio")
        params["anio"] = anio
    
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
            EXTRACT(HOUR FROM fecha_hecho)::int as hora,
            COUNT(*) as total_eventos
        FROM fact_seguridad
        WHERE {where_sql}
        GROUP BY hora
        ORDER BY hora
    """)
    
    results = db.execute(query, params).fetchall()
    
    # Clasificar por franjas horarias
    madrugada = sum(r[1] for r in results if r[0] in range(0, 6))
    manana = sum(r[1] for r in results if r[0] in range(6, 12))
    tarde = sum(r[1] for r in results if r[0] in range(12, 18))
    noche = sum(r[1] for r in results if r[0] in range(18, 24))
    
    return {
        "filtros": {
            "anio": anio,
            "municipio": municipio,
            "categoria": categoria
        },
        "distribucion_horaria": [
            {"hora": r[0], "total": r[1]} for r in results
        ],
        "franjas_horarias": {
            "madrugada_00_06": madrugada,
            "manana_06_12": manana,
            "tarde_12_18": tarde,
            "noche_18_24": noche
        },
        "hora_pico": max(results, key=lambda x: x[1]) if results else None
    }
