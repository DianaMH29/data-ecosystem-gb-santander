"""
Modelo: fact_seguridad - Tabla de Hechos (Target Variable)
"""
from sqlalchemy import Column, BigInteger, Integer, String, Date, Float, ForeignKey
from geoalchemy2 import Geometry
from ..database import Base


class FactSeguridad(Base):
    """
    Registro unificado de eventos delictivos.
    """
    __tablename__ = "fact_seguridad"
    
    id_evento = Column(BigInteger, primary_key=True, autoincrement=True,
                       comment="PK Autoincremental")
    fecha_hecho = Column(Date, index=True,
                         comment="Fecha del suceso")
    codigo_dane = Column(Integer, ForeignKey("master_municipios.codigo_dane"), index=True,
                         comment="FK -> master_municipios")
    categoria_delito = Column(String, index=True,
                              comment="Macro-tipo: HURTO, HOMICIDIO, SEXUAL, VIF, LESIONES")
    modalidad_especifica = Column(String,
                                  comment="Detalle (ej. A PERSONAS, RIÑA)")
    zona_hecho = Column(String,
                        comment="Contexto: URBANA, RURAL, VIAS PUBLICAS")
    clase_sitio = Column(String,
                         comment="Lugar específico: VÍA PÚBLICA, LOCAL COMERCIAL, etc.")
    genero = Column(String,
                    comment="Género de la víctima: MASCULINO, FEMENINO, etc.")
    grupo_etario = Column(String,
                          comment="Grupo de edad: MENOR, ADULTO, ADULTO MAYOR")
    arma_medio = Column(String,
                        comment="Mecanismo: ARMA DE FUEGO, SIN EMPLEO DE ARMAS, etc.")
    cantidad = Column(Integer, default=1,
                      comment="Número de víctimas/casos")
    latitud = Column(Float,
                     comment="Latitud de la ubicación")
    longitud = Column(Float,
                      comment="Longitud de la ubicación")
    geom = Column(Geometry("POINT", srid=4326),
                  comment="Ubicación exacta. Base para Heatmaps")
