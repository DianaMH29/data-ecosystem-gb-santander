"""
Modelo: master_infraestructura_poi - Dimensión de Entorno
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from geoalchemy2 import Geometry
from ..database import Base


class MasterInfraestructuraPoi(Base):
    """
    Puntos de interés estratégico (Oferta Institucional).
    """
    __tablename__ = "master_infraestructura_poi"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_dane = Column(Integer, ForeignKey("master_municipios.codigo_dane"), index=True,
                         comment="FK -> master_municipios")
    tipo_infraestructura = Column(String,
                                  comment="Categoría: COLEGIO, BIBLIOTECA")
    nombre_sede = Column(String,
                         comment="Nombre del establecimiento")
    zona_geo = Column(String,
                      comment="Ubicación: URBANA / RURAL")
    geom = Column(Geometry("POINT", srid=4326),
                  comment="Ubicación exacta del punto")
