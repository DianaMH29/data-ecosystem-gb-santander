"""
Módulo Base del Chatbot
Configuración de Gemini, conexión a DB y funciones auxiliares
"""

import os
import google.generativeai as genai
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.municipios import MasterMunicipios

# ============================================
# CONFIGURACIÓN DE GEMINI
# ============================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Modelo de Gemini
modelo_gemini = genai.GenerativeModel('gemini-2.0-flash')

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def resolver_municipio(db: Session, nombre_municipio: str) -> int | None:
    """
    Resuelve un nombre de municipio (parcial o completo) a su codigo_dane.
    Retorna None si no encuentra coincidencia.
    """
    # Búsqueda exacta (case insensitive)
    municipio = db.query(MasterMunicipios).filter(
        MasterMunicipios.nombre_municipio.ilike(nombre_municipio)
    ).first()
    
    if municipio:
        return municipio.codigo_dane
    
    # Búsqueda parcial
    municipio = db.query(MasterMunicipios).filter(
        MasterMunicipios.nombre_municipio.ilike(f"%{nombre_municipio}%")
    ).first()
    
    if municipio:
        return municipio.codigo_dane
    
    return None


def obtener_nombre_municipio(db: Session, codigo_dane: int) -> str:
    """Obtiene el nombre del municipio dado su codigo_dane"""
    municipio = db.query(MasterMunicipios).filter(
        MasterMunicipios.codigo_dane == codigo_dane
    ).first()
    return municipio.nombre_municipio if municipio else str(codigo_dane)


def limpiar_valor(valor: str | None) -> str | None:
    """Limpia valores nulos o vacíos"""
    if valor is None:
        return None
    valor = valor.strip()
    if valor.upper() in ['NULL', 'NONE', '', 'NINGUNO', 'TODOS']:
        return None
    return valor


def obtener_estadisticas_generales(db: Session) -> dict:
    """
    Obtiene estadísticas generales de toda la base de datos.
    Útil para responder preguntas generales.
    """
    query = text("""
        SELECT 
            COUNT(*) as total_eventos,
            COUNT(DISTINCT codigo_dane) as total_municipios,
            COUNT(DISTINCT categoria_delito) as total_categorias,
            MIN(fecha_hecho) as fecha_inicio,
            MAX(fecha_hecho) as fecha_fin
        FROM fact_seguridad
    """)
    
    result = db.execute(query).fetchone()
    
    return {
        "total_eventos": result.total_eventos,
        "total_municipios": result.total_municipios,
        "total_categorias": result.total_categorias,
        "periodo": f"{result.fecha_inicio} a {result.fecha_fin}"
    }


def obtener_opciones_disponibles(db: Session) -> dict:
    """
    Obtiene todas las opciones disponibles en la base de datos
    para ayudar al modelo a entender qué datos puede consultar.
    """
    categorias = db.execute(text("""
        SELECT DISTINCT categoria_delito FROM fact_seguridad 
        WHERE categoria_delito IS NOT NULL ORDER BY categoria_delito
    """)).fetchall()
    
    generos = db.execute(text("""
        SELECT DISTINCT genero FROM fact_seguridad 
        WHERE genero IS NOT NULL ORDER BY genero
    """)).fetchall()
    
    grupos_etarios = db.execute(text("""
        SELECT DISTINCT grupo_etario FROM fact_seguridad 
        WHERE grupo_etario IS NOT NULL ORDER BY grupo_etario
    """)).fetchall()
    
    zonas = db.execute(text("""
        SELECT DISTINCT zona FROM fact_seguridad 
        WHERE zona IS NOT NULL ORDER BY zona
    """)).fetchall()
    
    armas = db.execute(text("""
        SELECT DISTINCT arma_medio FROM fact_seguridad 
        WHERE arma_medio IS NOT NULL ORDER BY arma_medio
    """)).fetchall()
    
    modalidades = db.execute(text("""
        SELECT DISTINCT modalidad_especifica FROM fact_seguridad 
        WHERE modalidad_especifica IS NOT NULL ORDER BY modalidad_especifica LIMIT 50
    """)).fetchall()
    
    clases_sitio = db.execute(text("""
        SELECT DISTINCT clase_sitio FROM fact_seguridad 
        WHERE clase_sitio IS NOT NULL ORDER BY clase_sitio LIMIT 50
    """)).fetchall()
    
    anios = db.execute(text("""
        SELECT DISTINCT EXTRACT(YEAR FROM fecha_hecho)::int as anio 
        FROM fact_seguridad ORDER BY anio
    """)).fetchall()
    
    municipios = db.execute(text("""
        SELECT municipio FROM master_municipios ORDER BY municipio
    """)).fetchall()
    
    return {
        "categorias_delito": [r[0] for r in categorias],
        "generos": [r[0] for r in generos],
        "grupos_etarios": [r[0] for r in grupos_etarios],
        "zonas": [r[0] for r in zonas],
        "armas_medios": [r[0] for r in armas],
        "modalidades": [r[0] for r in modalidades][:20],  # Limitado
        "clases_sitio": [r[0] for r in clases_sitio][:20],  # Limitado
        "anios": [r[0] for r in anios],
        "municipios": [r[0] for r in municipios]
    }


# ============================================
# PROMPT DE SISTEMA PARA GEMINI
# ============================================

SYSTEM_PROMPT = """
Eres un asistente experto en análisis de datos de seguridad del departamento de Santander, Colombia.
Tu rol es ayudar a los usuarios a entender los datos de criminalidad de la región.

REGLAS IMPORTANTES:
1. Responde siempre en español
2. Sé conciso pero informativo
3. Usa números y porcentajes cuando sea relevante
4. Si no tienes datos suficientes, indica qué información adicional necesitas
5. Contextualiza los datos (ej: comparar con promedios, tendencias)
6. No inventes datos - solo usa la información proporcionada
7. Si la pregunta no está relacionada con seguridad/criminalidad en Santander, indica amablemente que solo puedes responder sobre ese tema

DATOS DISPONIBLES:
- Eventos de seguridad desde 2003 hasta 2025
- 87 municipios de Santander
- Categorías de delitos: HURTO, VIF (Violencia Intrafamiliar), SEXUAL, LESIONES, INFANCIA
- Información demográfica: género, grupo etario, zona (urbana/rural)
- Información del hecho: arma/medio, modalidad, clase de sitio
- Datos climáticos asociados (precipitación, temperatura)

FORMATO DE RESPUESTA:
- Usa viñetas para listas
- Usa negritas para datos importantes
- Incluye conclusiones o insights cuando sea apropiado
"""


def generar_respuesta_natural(db: Session, pregunta: str, datos: dict) -> str:
    """
    Genera una respuesta en lenguaje natural usando Gemini
    basándose en los datos obtenidos de la base de datos.
    """
    prompt = f"""
{SYSTEM_PROMPT}

PREGUNTA DEL USUARIO: {pregunta}

DATOS OBTENIDOS DE LA BASE DE DATOS:
{datos}

Por favor, genera una respuesta clara y útil basada en estos datos.
Si los datos están vacíos o son insuficientes, indica que no se encontraron resultados para esa consulta.
"""
    
    try:
        response = modelo_gemini.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error al generar respuesta: {str(e)}"
