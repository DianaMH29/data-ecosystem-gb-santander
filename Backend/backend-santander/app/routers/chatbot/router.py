"""
Router principal del Chatbot
Integra todos los módulos y expone los endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import re

from app.database import get_db
from .chatbot_base import modelo_gemini, obtener_estadisticas_generales
from .chatbot_geografia import (
    obtener_datos_municipio,
    obtener_ranking_municipios,
    obtener_ranking_por_tasa,
    comparar_municipios
)
from .chatbot_temporal import (
    obtener_tendencia_anual,
    obtener_datos_por_mes,
    obtener_datos_por_dia_semana,
    obtener_datos_rango_fechas,
    obtener_datos_fecha_especifica,
    obtener_comparativa_periodos
)
from .chatbot_victimas import (
    obtener_distribucion_genero,
    obtener_distribucion_grupo_etario,
    obtener_distribucion_zona,
    obtener_perfil_victima
)
from .chatbot_delitos import (
    obtener_datos_por_categoria,
    obtener_datos_por_modalidad,
    obtener_datos_por_arma,
    obtener_datos_por_sitio,
    obtener_ranking_categorias,
    obtener_ranking_modalidades,
    obtener_ranking_armas,
    obtener_ranking_sitios
)
from .chatbot_clima import (
    obtener_correlacion_clima_delitos,
    obtener_eventos_por_temperatura,
    obtener_eventos_por_precipitacion,
    obtener_resumen_climatico
)

router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"]
)


# ============================================
# MODELOS PYDANTIC
# ============================================

class PreguntaChat(BaseModel):
    pregunta: str
    contexto: Optional[str] = None


class RespuestaChat(BaseModel):
    respuesta: str
    datos_consultados: Optional[dict] = None
    tipo_consulta: Optional[str] = None


# ============================================
# PROMPT DE INTERPRETACIÓN
# ============================================

PROMPT_INTERPRETACION = """
Eres un asistente experto en análisis de datos de seguridad de Santander, Colombia.
Tu trabajo es interpretar preguntas en lenguaje natural y extraer los parámetros de consulta.

DATOS DISPONIBLES:
- Eventos de seguridad (2003-2025)
- 87 municipios de Santander
- Categorías de delitos: HURTO, VIF (Violencia Intrafamiliar), SEXUAL, LESIONES, INFANCIA
- Datos demográficos: género (MASCULINO, FEMENINO), grupos etarios (MENORES, ADOLESCENTES, JOVENES, ADULTOS, ADULTOS MAYORES)
- Zonas: URBANA, RURAL
- Modalidades específicas de cada delito
- Armas/medios utilizados
- Clase de sitio (VIA PUBLICA, VIVIENDA, etc.)
- Datos climáticos (2005-2019): precipitación

REGLAS IMPORTANTES PARA ELEGIR EL TIPO DE CONSULTA:
- Si la pregunta menciona GÉNERO (hombre, mujer, masculino, femenino) -> usa "genero"
- Si la pregunta menciona EDAD o grupo etario (niños, adolescentes, adultos, mayores) -> usa "grupo_etario"
- Si la pregunta menciona ZONA (urbano, rural, campo, ciudad) -> usa "zona"
- Si la pregunta es sobre un MUNICIPIO específico sin mencionar género/edad/zona -> usa "municipio"
- Si la pregunta pide RANKING o comparación de municipios -> usa "ranking" o "ranking_tasa"
- Si la pregunta es sobre TENDENCIA en el tiempo -> usa "tendencia_anual"
- Si la pregunta es sobre MESES o estacionalidad -> usa "datos_mes"
- Si la pregunta es sobre DÍAS de la semana -> usa "dia_semana"
- Si la pregunta es sobre CLIMA o lluvia -> usa "correlacion_clima"
- Si la pregunta es sobre QUÉ ARMA se usa más o ranking de armas -> usa "ranking_armas"
- Si la pregunta es sobre DÓNDE/LUGARES/SITIOS ocurren más delitos -> usa "ranking_sitios"

TIPOS DE CONSULTA DISPONIBLES:
1. "estadisticas_generales" - Resumen general de todos los datos
2. "municipio" - Datos de un municipio específico (sin filtro de género/edad/zona)
3. "ranking" - Top/Bottom municipios por cantidad de eventos
4. "ranking_tasa" - Top/Bottom municipios por tasa (por 100,000 habitantes)
5. "comparar_municipios" - Comparar dos o más municipios
6. "tendencia_anual" - Evolución por años
7. "datos_mes" - Distribución mensual de eventos
8. "dia_semana" - Análisis por día de la semana
9. "rango_fechas" - Datos en un rango de fechas específico
10. "genero" - Distribución por género (USAR cuando pregunten por hombres/mujeres/género)
11. "grupo_etario" - Análisis por grupo de edad
12. "zona" - Comparativa urbano vs rural
13. "categoria" - Datos de una categoría de delito específica
14. "modalidad" - Análisis por modalidad específica
15. "arma_medio" - Análisis de un arma/medio específico
16. "ranking_armas" - Ranking de armas/medios más usados
17. "ranking_sitios" - Ranking de lugares donde más ocurren delitos
18. "clase_sitio" - Análisis por tipo de lugar
19. "correlacion_clima" - Relación clima-delitos

IMPORTANTE: Todos los tipos de consulta aceptan filtros adicionales de municipio, año y categoría.
Por ejemplo, si preguntan "violencia sexual contra hombres en Barrancabermeja", 
debes usar tipo_consulta="genero" con parametros municipio="Barrancabermeja" y categoria="SEXUAL".

RESPONDE ÚNICAMENTE con un JSON válido con esta estructura:
{{
    "tipo_consulta": "nombre_del_tipo",
    "parametros": {{
        "municipio": "nombre del municipio si aplica",
        "municipios": ["lista", "de", "municipios"] si es comparación,
        "anio": número de año si aplica,
        "mes": número de mes (1-12) si aplica,
        "dia_semana": nombre del día si aplica,
        "fecha_inicio": "YYYY-MM-DD" si aplica,
        "fecha_fin": "YYYY-MM-DD" si aplica,
        "categoria": "categoría de delito si aplica (HURTO, VIF, SEXUAL, LESIONES, INFANCIA)",
        "modalidad": "modalidad específica si aplica",
        "arma_medio": "arma o medio si aplica",
        "clase_sitio": "tipo de sitio si aplica",
        "genero": "MASCULINO o FEMENINO si aplica",
        "grupo_etario": "grupo de edad si aplica",
        "zona": "URBANA o RURAL si aplica",
        "limite": número para rankings (default 10),
        "orden": "desc" o "asc" para rankings
    }}
}}

PREGUNTA DEL USUARIO: {pregunta}

Responde SOLO con el JSON, sin explicaciones adicionales.
"""

PROMPT_RESPUESTA = """
Eres un asistente experto en seguridad pública de Santander, Colombia.
Responde de manera clara, profesional y útil.

PREGUNTA ORIGINAL: {pregunta}

DATOS OBTENIDOS DE LA CONSULTA:
{datos}

Genera una respuesta natural y conversacional basada en los datos.
Incluye estadísticas relevantes y, si es apropiado, ofrece contexto o insights.
Si hay datos de población, menciona las tasas por 100,000 habitantes cuando sea relevante.
Sé conciso pero informativo.
"""


# ============================================
# FUNCIONES DE PROCESAMIENTO
# ============================================

def interpretar_pregunta(pregunta: str) -> dict:
    """
    Usa Gemini para interpretar la pregunta y extraer parámetros.
    """
    prompt = PROMPT_INTERPRETACION.format(pregunta=pregunta)
    
    try:
        respuesta = modelo_gemini.generate_content(prompt)
        texto = respuesta.text.strip()
        
        # Limpiar el texto de posibles marcadores de código
        if texto.startswith("```"):
            texto = re.sub(r'^```json?\n?', '', texto)
            texto = re.sub(r'\n?```$', '', texto)
        
        # Parsear JSON
        interpretacion = json.loads(texto)
        
        # Limpiar valores nulos
        if "parametros" in interpretacion:
            interpretacion["parametros"] = {
                k: v for k, v in interpretacion["parametros"].items()
                if v is not None and v != "null" and v != "None" and v != ""
            }
        
        return interpretacion
        
    except json.JSONDecodeError as e:
        return {"tipo_consulta": "estadisticas_generales", "parametros": {}, "error": f"Error parseando JSON: {e}"}
    except Exception as e:
        return {"tipo_consulta": "estadisticas_generales", "parametros": {}, "error": str(e)}


def ejecutar_consulta(db: Session, tipo_consulta: str, parametros: dict) -> dict:
    """
    Ejecuta la consulta apropiada según el tipo identificado.
    """
    try:
        if tipo_consulta == "estadisticas_generales":
            return obtener_estadisticas_generales(db)
        
        elif tipo_consulta == "municipio":
            return obtener_datos_municipio(
                db,
                parametros.get("municipio", "Bucaramanga"),
                parametros.get("anio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "ranking":
            return obtener_ranking_municipios(
                db,
                parametros.get("categoria"),
                parametros.get("anio"),
                parametros.get("limite", 10),
                parametros.get("orden", "desc")
            )
        
        elif tipo_consulta == "ranking_tasa":
            return obtener_ranking_por_tasa(
                db,
                parametros.get("categoria"),
                parametros.get("anio"),
                parametros.get("limite", 10),
                parametros.get("orden", "desc")
            )
        
        elif tipo_consulta == "comparar_municipios":
            municipios = parametros.get("municipios", [])
            if not municipios and parametros.get("municipio"):
                municipios = [parametros.get("municipio")]
            return comparar_municipios(
                db,
                municipios,
                parametros.get("anio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "tendencia_anual":
            return obtener_tendencia_anual(
                db,
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "datos_mes":
            return obtener_datos_por_mes(
                db,
                parametros.get("anio"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "dia_semana":
            return obtener_datos_por_dia_semana(
                db,
                parametros.get("anio"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "rango_fechas":
            return obtener_datos_rango_fechas(
                db,
                parametros.get("fecha_inicio"),
                parametros.get("fecha_fin"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "fecha_especifica":
            return obtener_datos_fecha_especifica(
                db,
                parametros.get("fecha"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "comparativa_periodos":
            return obtener_comparativa_periodos(
                db,
                parametros.get("anio_1"),
                parametros.get("anio_2"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "genero":
            return obtener_distribucion_genero(
                db,
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "grupo_etario":
            return obtener_distribucion_grupo_etario(
                db,
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "zona":
            return obtener_distribucion_zona(
                db,
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "perfil_victima":
            return obtener_perfil_victima(
                db,
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "categoria":
            return obtener_datos_por_categoria(
                db,
                parametros.get("categoria", "HURTO"),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        
        elif tipo_consulta == "modalidad":
            return obtener_datos_por_modalidad(
                db,
                parametros.get("modalidad"),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        
        elif tipo_consulta == "arma_medio":
            return obtener_datos_por_arma(
                db,
                parametros.get("arma_medio"),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        
        elif tipo_consulta == "clase_sitio":
            return obtener_datos_por_sitio(
                db,
                parametros.get("clase_sitio"),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        
        elif tipo_consulta == "ranking_categorias":
            return obtener_ranking_categorias(
                db,
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("limite", 10)
            )
        
        elif tipo_consulta == "ranking_armas":
            return obtener_ranking_armas(
                db,
                parametros.get("categoria"),
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("limite", 10)
            )
        
        elif tipo_consulta == "ranking_sitios":
            return obtener_ranking_sitios(
                db,
                parametros.get("categoria"),
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("limite", 10)
            )
        
        elif tipo_consulta == "correlacion_clima":
            return obtener_correlacion_clima_delitos(
                db,
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "clima_temperatura":
            return obtener_eventos_por_temperatura(
                db,
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "clima_precipitacion":
            return obtener_eventos_por_precipitacion(
                db,
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        elif tipo_consulta == "resumen_clima":
            return obtener_resumen_climatico(
                db,
                parametros.get("municipio")
            )
        
        else:
            return obtener_estadisticas_generales(db)
            
    except Exception as e:
        return {"error": f"Error ejecutando consulta: {str(e)}"}


def generar_respuesta_natural(pregunta: str, datos: dict) -> str:
    """
    Usa Gemini para generar una respuesta natural basada en los datos.
    """
    if "error" in datos:
        return f"Lo siento, hubo un problema al consultar los datos: {datos['error']}"
    
    prompt = PROMPT_RESPUESTA.format(
        pregunta=pregunta,
        datos=json.dumps(datos, ensure_ascii=False, indent=2, default=str)
    )
    
    try:
        respuesta = modelo_gemini.generate_content(prompt)
        return respuesta.text.strip()
    except Exception as e:
        # Si falla Gemini, dar respuesta básica
        return f"Datos encontrados: {json.dumps(datos, ensure_ascii=False, default=str)[:500]}..."


# ============================================
# ENDPOINTS
# ============================================

@router.post("/consultar", response_model=RespuestaChat)
async def consultar_chatbot(
    pregunta_data: PreguntaChat,
    db: Session = Depends(get_db)
):
    """
    Endpoint principal del chatbot.
    Recibe una pregunta en lenguaje natural y devuelve una respuesta.
    """
    pregunta = pregunta_data.pregunta
    
    # 1. Interpretar la pregunta
    interpretacion = interpretar_pregunta(pregunta)
    tipo_consulta = interpretacion.get("tipo_consulta", "estadisticas_generales")
    parametros = interpretacion.get("parametros", {})
    
    # 2. Ejecutar la consulta
    datos = ejecutar_consulta(db, tipo_consulta, parametros)
    
    # 3. Generar respuesta natural
    respuesta = generar_respuesta_natural(pregunta, datos)
    
    return RespuestaChat(
        respuesta=respuesta,
        datos_consultados=datos,
        tipo_consulta=tipo_consulta
    )


@router.get("/sugerencias")
async def obtener_sugerencias():
    """
    Devuelve una lista de preguntas sugeridas para el chatbot.
    """
    return {
        "sugerencias": [
            # Geográficas
            "¿Cuáles son las estadísticas de criminalidad en Bucaramanga?",
            "¿Cuál es el municipio con más delitos en Santander?",
            "¿Cuáles son los 5 municipios más seguros por tasa de criminalidad?",
            "Compara la criminalidad entre Bucaramanga y Floridablanca",
            
            # Temporales
            "¿Cómo ha evolucionado el crimen en los últimos 10 años?",
            "¿En qué mes hay más delitos?",
            "¿Qué día de la semana ocurren más crímenes?",
            "¿Cuántos delitos hubo entre enero y junio de 2023?",
            "¿Cómo fue la evolución mensual del crimen en 2023?",
            
            # Demográficas
            "¿Qué género es más afectado por la violencia?",
            "¿Cuál es el grupo de edad más vulnerable?",
            "¿Hay más delitos en zonas urbanas o rurales?",
            
            # Por tipo de delito
            "¿Cuántos casos de hurto hay registrados?",
            "¿Cuál es la modalidad más común de hurto?",
            "¿Qué arma se usa más en los delitos?",
            "¿En qué lugares ocurren más delitos?",
            
            # Climáticas
            "¿Hay relación entre el clima y los delitos?",
            "¿Cómo afecta la temperatura a los hurtos?",
            
            # Combinadas
            "¿Cuántos casos de violencia intrafamiliar hay en Bucaramanga en 2023?",
            "¿Cuál es la tendencia de delitos sexuales en zona rural?",
            "¿Qué municipio tiene más hurtos por habitante?"
        ],
        "categorias": {
            "geograficas": [
                "Estadísticas por municipio",
                "Rankings de municipios",
                "Comparaciones entre municipios"
            ],
            "temporales": [
                "Tendencias anuales",
                "Análisis mensual",
                "Análisis por día de semana",
                "Rangos de fechas"
            ],
            "demograficas": [
                "Por género",
                "Por grupo etario",
                "Por zona (urbana/rural)"
            ],
            "delitos": [
                "Por categoría (HURTO, VIF, SEXUAL, LESIONES, INFANCIA)",
                "Por modalidad específica",
                "Por arma/medio utilizado",
                "Por clase de sitio"
            ],
            "clima": [
                "Correlación clima-delitos",
                "Análisis climático por tipo de delito"
            ]
        }
    }


@router.get("/capacidades")
async def obtener_capacidades():
    """
    Devuelve las capacidades completas del chatbot.
    """
    return {
        "descripcion": "Chatbot de análisis de seguridad de Santander",
        "datos_disponibles": {
            "periodo": "2003-2025",
            "municipios": 87,
            "categorias_delito": ["HURTO", "VIF", "SEXUAL", "LESIONES", "INFANCIA"],
            "datos_clima": "2005-2019"
        },
        "tipos_consulta": [
            {"tipo": "estadisticas_generales", "descripcion": "Resumen general de todos los datos"},
            {"tipo": "municipio", "descripcion": "Estadísticas de un municipio específico"},
            {"tipo": "ranking", "descripcion": "Top/Bottom municipios por cantidad"},
            {"tipo": "ranking_tasa", "descripcion": "Top/Bottom municipios por tasa (por 100k habitantes)"},
            {"tipo": "comparar_municipios", "descripcion": "Comparación entre varios municipios"},
            {"tipo": "tendencia_anual", "descripcion": "Evolución año a año"},
            {"tipo": "datos_mes", "descripcion": "Análisis de un mes específico"},
            {"tipo": "dia_semana", "descripcion": "Distribución por día de la semana"},
            {"tipo": "rango_fechas", "descripcion": "Datos en un período específico"},
            {"tipo": "evolucion_mensual", "descripcion": "Tendencia mes a mes"},
            {"tipo": "genero", "descripcion": "Comparativa por género"},
            {"tipo": "grupo_etario", "descripcion": "Análisis por grupo de edad"},
            {"tipo": "zona", "descripcion": "Comparativa urbano vs rural"},
            {"tipo": "categoria", "descripcion": "Análisis de una categoría de delito"},
            {"tipo": "modalidad", "descripcion": "Análisis por modalidad específica"},
            {"tipo": "arma_medio", "descripcion": "Análisis por arma o medio utilizado"},
            {"tipo": "clase_sitio", "descripcion": "Análisis por tipo de lugar"},
            {"tipo": "correlacion_clima", "descripcion": "Relación entre clima y delitos"},
            {"tipo": "clima_delito", "descripcion": "Clima asociado a tipo de delito"}
        ],
        "filtros_disponibles": [
            "municipio", "anio", "mes", "dia_semana",
            "fecha_inicio", "fecha_fin", "categoria",
            "modalidad", "arma_medio", "clase_sitio",
            "genero", "grupo_etario", "zona"
        ]
    }


@router.get("/estadisticas")
async def estadisticas_rapidas(db: Session = Depends(get_db)):
    """
    Devuelve estadísticas generales rápidas.
    """
    return obtener_estadisticas_generales(db)
