"""
Router Principal del Chatbot
Integra todos los módulos y expone los endpoints de la API
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
import json

from app.database import get_db

# Importar módulos del chatbot
from .chatbot.chatbot_base import (
    modelo_gemini,
    obtener_estadisticas_generales,
    obtener_opciones_disponibles,
    generar_respuesta_natural,
    limpiar_valor,
    SYSTEM_PROMPT
)
from .chatbot.chatbot_geografia import (
    obtener_datos_municipio,
    obtener_ranking_municipios,
    obtener_ranking_por_tasa,
    comparar_municipios,
    obtener_municipios_cercanos
)
from .chatbot.chatbot_temporal import (
    obtener_tendencia_anual,
    obtener_datos_por_mes,
    obtener_datos_por_dia_semana,
    obtener_datos_rango_fechas,
    obtener_datos_fecha_especifica,
    obtener_comparativa_periodos,
    obtener_horario_eventos
)
from .chatbot.chatbot_victimas import (
    obtener_distribucion_genero,
    obtener_distribucion_grupo_etario,
    obtener_distribucion_zona,
    obtener_perfil_victima,
    obtener_vulnerabilidad_por_delito,
    comparar_genero_por_anio,
    obtener_ranking_municipios_por_genero
)
from .chatbot.chatbot_delitos import (
    obtener_datos_por_categoria,
    obtener_datos_por_modalidad,
    obtener_datos_por_arma,
    obtener_datos_por_sitio,
    obtener_ranking_categorias,
    obtener_ranking_modalidades,
    obtener_ranking_armas,
    obtener_ranking_sitios,
    comparar_categorias
)
from .chatbot.chatbot_clima import (
    obtener_correlacion_clima_delitos,
    obtener_eventos_por_precipitacion,
    obtener_eventos_por_temperatura,
    obtener_tendencia_climatica_mensual,
    obtener_dias_extremos,
    obtener_resumen_climatico
)


router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot IA"]
)


# ============================================
# MODELOS PYDANTIC
# ============================================

class PreguntaChat(BaseModel):
    pregunta: str
    contexto: Optional[dict] = None


class RespuestaChat(BaseModel):
    pregunta: str
    respuesta: str
    datos_consultados: Optional[dict] = None
    tipo_consulta: Optional[str] = None


# ============================================
# PROMPT DE INTERPRETACIÓN
# ============================================

PROMPT_INTERPRETACION = """
Analiza la siguiente pregunta del usuario y extrae los parámetros necesarios para consultarla.

PREGUNTA: {pregunta}

OPCIONES DISPONIBLES EN LA BASE DE DATOS:
{opciones}

Responde SOLO con un JSON válido (sin markdown, sin ```json, solo el JSON puro) con la siguiente estructura:
{{
    "tipo_consulta": "<tipo>",
    "parametros": {{...}}
}}

TIPOS DE CONSULTA DISPONIBLES:

1. GEOGRAFÍA:
   - "estadisticas_municipio": Info de un municipio
     parametros: {{"municipio": "<nombre>", "anio": <año|null>, "categoria": "<cat|null>"}}
   - "ranking_municipios": Top municipios por eventos
     parametros: {{"categoria": "<cat|null>", "anio": <año|null>, "limite": <n>, "orden": "desc|asc"}}
   - "ranking_tasa": Top municipios por tasa (por 100k habitantes)
     parametros: {{"categoria": "<cat|null>", "anio": <año|null>, "limite": <n>, "orden": "desc|asc"}}
   - "comparar_municipios": Comparar varios municipios
     parametros: {{"municipios": ["<mun1>", "<mun2>", ...], "anio": <año|null>, "categoria": "<cat|null>"}}
   - "municipios_cercanos": Municipios cerca de uno dado
     parametros: {{"municipio": "<nombre>", "radio_km": <n>}}

2. TEMPORAL:
   - "tendencia_anual": Evolución por años
     parametros: {{"municipio": "<nombre|null>", "categoria": "<cat|null>", "anio_inicio": <año|null>, "anio_fin": <año|null>}}
   - "datos_mes": Distribución por mes
     parametros: {{"anio": <año|null>, "municipio": "<nombre|null>", "categoria": "<cat|null>"}}
   - "datos_dia_semana": Por día de la semana
     parametros: {{"anio": <año|null>, "municipio": "<nombre|null>", "categoria": "<cat|null>"}}
   - "rango_fechas": Datos entre dos fechas
     parametros: {{"fecha_inicio": "YYYY-MM-DD", "fecha_fin": "YYYY-MM-DD", "municipio": "<nombre|null>", "categoria": "<cat|null>"}}
   - "fecha_especifica": Eventos de un día concreto
     parametros: {{"fecha": "YYYY-MM-DD", "municipio": "<nombre|null>"}}
   - "comparar_periodos": Comparar dos años
     parametros: {{"anio_1": <año>, "anio_2": <año>, "municipio": "<nombre|null>", "categoria": "<cat|null>"}}
   - "horario_eventos": Distribución por hora
     parametros: {{"anio": <año|null>, "municipio": "<nombre|null>", "categoria": "<cat|null>"}}

3. VÍCTIMAS/DEMOGRAFÍA:
   - "distribucion_genero": Por género
     parametros: {{"municipio": "<nombre|null>", "anio": <año|null>, "categoria": "<cat|null>"}}
   - "distribucion_edad": Por grupo etario
     parametros: {{"municipio": "<nombre|null>", "anio": <año|null>, "categoria": "<cat|null>", "genero": "<gen|null>"}}
   - "distribucion_zona": Por zona urbana/rural
     parametros: {{"municipio": "<nombre|null>", "anio": <año|null>, "categoria": "<cat|null>"}}
   - "perfil_victima": Perfil demográfico completo
     parametros: {{"municipio": "<nombre|null>", "anio": <año|null>, "categoria": "<cat|null>"}}
   - "vulnerabilidad": Grupos más vulnerables por delito
     parametros: {{"anio": <año|null>, "municipio": "<nombre|null>"}}
   - "tendencia_genero": Evolución por género en el tiempo
     parametros: {{"municipio": "<nombre|null>", "categoria": "<cat|null>"}}
   - "ranking_por_genero": Municipios con más eventos de un género
     parametros: {{"genero": "<MASCULINO|FEMENINO>", "anio": <año|null>, "categoria": "<cat|null>", "limite": <n>}}

4. DELITOS:
   - "datos_categoria": Info detallada de una categoría
     parametros: {{"categoria": "<cat>", "municipio": "<nombre|null>", "anio": <año|null>}}
   - "datos_modalidad": Por modalidad específica
     parametros: {{"modalidad": "<mod>", "municipio": "<nombre|null>", "anio": <año|null>}}
   - "datos_arma": Por arma/medio utilizado
     parametros: {{"arma": "<arma>", "municipio": "<nombre|null>", "anio": <año|null>}}
   - "datos_sitio": Por clase de sitio
     parametros: {{"clase_sitio": "<sitio>", "municipio": "<nombre|null>", "anio": <año|null>}}
   - "ranking_categorias": Ranking de categorías
     parametros: {{"municipio": "<nombre|null>", "anio": <año|null>}}
   - "ranking_modalidades": Ranking de modalidades
     parametros: {{"categoria": "<cat|null>", "municipio": "<nombre|null>", "anio": <año|null>", "limite": <n>}}
   - "ranking_armas": Ranking de armas/medios
     parametros: {{"categoria": "<cat|null>", "municipio": "<nombre|null>", "anio": <año|null>", "limite": <n>}}
   - "ranking_sitios": Ranking de clases de sitio
     parametros: {{"categoria": "<cat|null>", "municipio": "<nombre|null>", "anio": <año|null>", "limite": <n>}}
   - "comparar_categorias": Comparar categorías
     parametros: {{"categorias": ["<cat1>", "<cat2>"], "municipio": "<nombre|null>", "anio": <año|null>}}

5. CLIMA:
   - "correlacion_clima": Relación clima-delitos
     parametros: {{"municipio": "<nombre|null>", "categoria": "<cat|null>", "anio": <año|null>}}
   - "eventos_lluvia": Eventos por nivel de lluvia
     parametros: {{"nivel": "alta|media|baja|sin_lluvia", "municipio": "<nombre|null>", "anio": <año|null>}}
   - "eventos_temperatura": Eventos por temperatura
     parametros: {{"rango": "frio|templado|calido", "municipio": "<nombre|null>", "anio": <año|null>}}
   - "tendencia_clima_mensual": Clima y delitos por mes
     parametros: {{"municipio": "<nombre|null>", "anio": <año|null>}}
   - "dias_extremos": Días con condiciones extremas
     parametros: {{"tipo": "mas_lluvioso|mas_caliente|mas_frio|mas_eventos", "municipio": "<nombre|null>", "anio": <año|null>", "limite": <n>}}
   - "resumen_clima": Resumen climático general
     parametros: {{"municipio": "<nombre|null>", "anio": <año|null>}}

6. GENERAL:
   - "estadisticas_generales": Resumen general de la base de datos
     parametros: {{}}

IMPORTANTE:
- Si no se menciona un filtro, usa null
- Los años van de 2003 a 2025
- Las categorías son: HURTO, VIF, SEXUAL, LESIONES, INFANCIA
- Los géneros son: MASCULINO, FEMENINO
- Si la pregunta es muy general o ambigua, usa "estadisticas_generales"
- Si mencionan "densidad", "tasa", "por habitante", usa ranking_tasa
- Si mencionan "lunes", "martes", etc., usa datos_dia_semana
- Si mencionan "enero", "febrero", etc., usa datos_mes
- Responde SOLO el JSON, sin explicaciones adicionales
"""


def interpretar_pregunta(db: Session, pregunta: str) -> dict:
    """
    Usa Gemini para interpretar la pregunta y extraer parámetros.
    """
    opciones = obtener_opciones_disponibles(db)
    
    prompt = PROMPT_INTERPRETACION.format(
        pregunta=pregunta,
        opciones=json.dumps(opciones, ensure_ascii=False, indent=2)
    )
    
    try:
        response = modelo_gemini.generate_content(prompt)
        texto = response.text.strip()
        
        # Limpiar posibles marcadores de código
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        texto = texto.strip()
        
        resultado = json.loads(texto)
        
        # Limpiar valores nulos/vacíos de los parámetros
        if "parametros" in resultado:
            resultado["parametros"] = {
                k: limpiar_valor(v) if isinstance(v, str) else v
                for k, v in resultado["parametros"].items()
            }
        
        return resultado
    except json.JSONDecodeError as e:
        return {
            "tipo_consulta": "estadisticas_generales",
            "parametros": {},
            "error_parsing": str(e)
        }
    except Exception as e:
        return {
            "tipo_consulta": "error",
            "parametros": {},
            "error": str(e)
        }


def ejecutar_consulta(db: Session, tipo_consulta: str, parametros: dict) -> dict:
    """
    Ejecuta la consulta correspondiente según el tipo detectado.
    """
    try:
        # GEOGRAFÍA
        if tipo_consulta == "estadisticas_municipio":
            return obtener_datos_municipio(
                db,
                parametros.get("municipio", ""),
                parametros.get("anio"),
                parametros.get("categoria")
            )
        elif tipo_consulta == "ranking_municipios":
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
            return comparar_municipios(
                db,
                parametros.get("municipios", []),
                parametros.get("anio"),
                parametros.get("categoria")
            )
        elif tipo_consulta == "municipios_cercanos":
            return obtener_municipios_cercanos(
                db,
                parametros.get("municipio", ""),
                parametros.get("radio_km", 50)
            )
        
        # TEMPORAL
        elif tipo_consulta == "tendencia_anual":
            return obtener_tendencia_anual(
                db,
                parametros.get("municipio"),
                parametros.get("categoria"),
                parametros.get("anio_inicio"),
                parametros.get("anio_fin")
            )
        elif tipo_consulta == "datos_mes":
            return obtener_datos_por_mes(
                db,
                parametros.get("anio"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        elif tipo_consulta == "datos_dia_semana":
            return obtener_datos_por_dia_semana(
                db,
                parametros.get("anio"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        elif tipo_consulta == "rango_fechas":
            return obtener_datos_rango_fechas(
                db,
                parametros.get("fecha_inicio", "2020-01-01"),
                parametros.get("fecha_fin", "2024-12-31"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        elif tipo_consulta == "fecha_especifica":
            return obtener_datos_fecha_especifica(
                db,
                parametros.get("fecha", "2023-01-01"),
                parametros.get("municipio")
            )
        elif tipo_consulta == "comparar_periodos":
            return obtener_comparativa_periodos(
                db,
                parametros.get("anio_1", 2022),
                parametros.get("anio_2", 2023),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        elif tipo_consulta == "horario_eventos":
            return obtener_horario_eventos(
                db,
                parametros.get("anio"),
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        
        # VÍCTIMAS
        elif tipo_consulta == "distribucion_genero":
            return obtener_distribucion_genero(
                db,
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("categoria")
            )
        elif tipo_consulta == "distribucion_edad":
            return obtener_distribucion_grupo_etario(
                db,
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("categoria"),
                parametros.get("genero")
            )
        elif tipo_consulta == "distribucion_zona":
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
        elif tipo_consulta == "vulnerabilidad":
            return obtener_vulnerabilidad_por_delito(
                db,
                parametros.get("anio"),
                parametros.get("municipio")
            )
        elif tipo_consulta == "tendencia_genero":
            return comparar_genero_por_anio(
                db,
                parametros.get("municipio"),
                parametros.get("categoria")
            )
        elif tipo_consulta == "ranking_por_genero":
            return obtener_ranking_municipios_por_genero(
                db,
                parametros.get("genero", "FEMENINO"),
                parametros.get("anio"),
                parametros.get("categoria"),
                parametros.get("limite", 10)
            )
        
        # DELITOS
        elif tipo_consulta == "datos_categoria":
            return obtener_datos_por_categoria(
                db,
                parametros.get("categoria", "HURTO"),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        elif tipo_consulta == "datos_modalidad":
            return obtener_datos_por_modalidad(
                db,
                parametros.get("modalidad", ""),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        elif tipo_consulta == "datos_arma":
            return obtener_datos_por_arma(
                db,
                parametros.get("arma", ""),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        elif tipo_consulta == "datos_sitio":
            return obtener_datos_por_sitio(
                db,
                parametros.get("clase_sitio", ""),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        elif tipo_consulta == "ranking_categorias":
            return obtener_ranking_categorias(
                db,
                parametros.get("municipio"),
                parametros.get("anio")
            )
        elif tipo_consulta == "ranking_modalidades":
            return obtener_ranking_modalidades(
                db,
                parametros.get("categoria"),
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("limite", 20)
            )
        elif tipo_consulta == "ranking_armas":
            return obtener_ranking_armas(
                db,
                parametros.get("categoria"),
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("limite", 20)
            )
        elif tipo_consulta == "ranking_sitios":
            return obtener_ranking_sitios(
                db,
                parametros.get("categoria"),
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("limite", 20)
            )
        elif tipo_consulta == "comparar_categorias":
            return comparar_categorias(
                db,
                parametros.get("categorias", ["HURTO", "VIF"]),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        
        # CLIMA
        elif tipo_consulta == "correlacion_clima":
            return obtener_correlacion_clima_delitos(
                db,
                parametros.get("municipio"),
                parametros.get("categoria"),
                parametros.get("anio")
            )
        elif tipo_consulta == "eventos_lluvia":
            return obtener_eventos_por_precipitacion(
                db,
                parametros.get("nivel", "alta"),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        elif tipo_consulta == "eventos_temperatura":
            return obtener_eventos_por_temperatura(
                db,
                parametros.get("rango", "calido"),
                parametros.get("municipio"),
                parametros.get("anio")
            )
        elif tipo_consulta == "tendencia_clima_mensual":
            return obtener_tendencia_climatica_mensual(
                db,
                parametros.get("municipio"),
                parametros.get("anio")
            )
        elif tipo_consulta == "dias_extremos":
            return obtener_dias_extremos(
                db,
                parametros.get("tipo", "mas_eventos"),
                parametros.get("municipio"),
                parametros.get("anio"),
                parametros.get("limite", 10)
            )
        elif tipo_consulta == "resumen_clima":
            return obtener_resumen_climatico(
                db,
                parametros.get("municipio"),
                parametros.get("anio")
            )
        
        # GENERAL
        elif tipo_consulta == "estadisticas_generales":
            return obtener_estadisticas_generales(db)
        
        else:
            return obtener_estadisticas_generales(db)
            
    except Exception as e:
        return {"error": str(e)}


# ============================================
# ENDPOINTS
# ============================================

@router.post("/preguntar", response_model=RespuestaChat)
async def preguntar(
    pregunta_chat: PreguntaChat,
    db: Session = Depends(get_db)
):
    """
    Endpoint principal del chatbot.
    Recibe una pregunta en lenguaje natural y devuelve una respuesta contextualizada.
    """
    pregunta = pregunta_chat.pregunta.strip()
    
    if not pregunta:
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
    
    # 1. Interpretar la pregunta
    interpretacion = interpretar_pregunta(db, pregunta)
    tipo_consulta = interpretacion.get("tipo_consulta", "estadisticas_generales")
    parametros = interpretacion.get("parametros", {})
    
    # 2. Ejecutar la consulta
    datos = ejecutar_consulta(db, tipo_consulta, parametros)
    
    # 3. Generar respuesta natural con Gemini
    respuesta = generar_respuesta_natural(db, pregunta, datos)
    
    return RespuestaChat(
        pregunta=pregunta,
        respuesta=respuesta,
        datos_consultados=datos,
        tipo_consulta=tipo_consulta
    )


@router.get("/sugerencias")
async def obtener_sugerencias():
    """
    Devuelve una lista de preguntas sugeridas para el usuario.
    """
    return {
        "sugerencias": [
            # Geografía
            "¿Cuál es el municipio más peligroso de Santander?",
            "¿Cuáles son los municipios con mayor tasa de criminalidad por habitante?",
            "¿Cómo está la seguridad en Bucaramanga?",
            "Compara los delitos entre Bucaramanga y Floridablanca",
            "¿Qué municipios están cerca de Barrancabermeja?",
            
            # Temporal
            "¿Cuál ha sido la tendencia del crimen en los últimos años?",
            "¿En qué mes hay más delitos?",
            "¿Qué día de la semana ocurren más hurtos?",
            "¿Cómo se compara 2023 con 2022?",
            "¿Qué pasó el 31 de diciembre de 2023?",
            "¿A qué hora ocurren más delitos?",
            
            # Víctimas
            "¿Qué género es más afectado por la violencia?",
            "¿Cuál es el grupo de edad más vulnerable?",
            "¿Hay más delitos en zonas urbanas o rurales?",
            "¿Cuál es el perfil típico de las víctimas de VIF?",
            "¿Qué grupos son más vulnerables a cada tipo de delito?",
            
            # Delitos
            "¿Cuál es el delito más común en Santander?",
            "¿Cuáles son las modalidades más frecuentes de hurto?",
            "¿Qué armas se usan más en los delitos?",
            "¿En qué lugares ocurren más delitos sexuales?",
            "Compara los hurtos con la violencia intrafamiliar",
            
            # Clima
            "¿Cómo afecta la lluvia a la criminalidad?",
            "¿Hay más delitos cuando hace calor?",
            "¿Cuál es la relación entre el clima y los delitos?",
            "¿Cuáles fueron los días más lluviosos con más delitos?",
            
            # Combinadas
            "¿Cuántos hurtos hubo en Bucaramanga en 2023?",
            "¿Cuál es el delito más frecuente contra mujeres?",
            "¿En qué municipio hay más violencia intrafamiliar?"
        ]
    }


@router.get("/capacidades")
async def obtener_capacidades():
    """
    Devuelve información sobre las capacidades del chatbot.
    """
    return {
        "descripcion": "Chatbot de análisis de seguridad de Santander",
        "capacidades": {
            "geografia": [
                "Estadísticas por municipio",
                "Rankings de municipios (absoluto y por tasa)",
                "Comparación entre municipios",
                "Municipios cercanos geográficamente"
            ],
            "temporal": [
                "Tendencias anuales",
                "Distribución por mes",
                "Distribución por día de la semana",
                "Análisis por rango de fechas",
                "Eventos de fechas específicas",
                "Comparación entre períodos",
                "Distribución por hora del día"
            ],
            "victimas": [
                "Distribución por género",
                "Distribución por grupo etario",
                "Distribución por zona (urbana/rural)",
                "Perfil demográfico de víctimas",
                "Análisis de vulnerabilidad",
                "Tendencias de género por año"
            ],
            "delitos": [
                "Estadísticas por categoría de delito",
                "Análisis por modalidad específica",
                "Análisis por arma/medio utilizado",
                "Análisis por clase de sitio",
                "Rankings de categorías, modalidades, armas y sitios",
                "Comparación entre categorías"
            ],
            "clima": [
                "Correlación clima-delitos",
                "Eventos por nivel de precipitación",
                "Eventos por rango de temperatura",
                "Tendencia climática mensual",
                "Días con condiciones extremas",
                "Resumen climático general"
            ]
        },
        "datos_disponibles": {
            "periodo": "2003 - 2025",
            "municipios": 87,
            "categorias_delito": ["HURTO", "VIF", "SEXUAL", "LESIONES", "INFANCIA"],
            "datos_climaticos": "2005 - 2019"
        }
    }


@router.get("/opciones")
async def obtener_opciones_filtros(db: Session = Depends(get_db)):
    """
    Devuelve todas las opciones disponibles para filtros.
    """
    return obtener_opciones_disponibles(db)
