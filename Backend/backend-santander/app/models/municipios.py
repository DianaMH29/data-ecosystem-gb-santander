"""
Modelo: master_municipios - Dimensión Geográfica Principal
"""
from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from ..database import Base


class MasterMunicipios(Base):
    """
    Tabla principal que define la geometría y la identidad administrativa.
    Eje de todos los JOINs.
    """
    __tablename__ = "master_municipios"
    
    codigo_dane = Column(Integer, primary_key=True, index=True,
                         comment="Código oficial DANE (5 dígitos)")
    nombre_municipio = Column(String, nullable=False,
                              comment="Nombre normalizado del municipio")
    categoria_rural_urbana = Column(String,
                                    comment="Vocación: PREDOMINANTEMENTE RURAL o URBANA")
    geom = Column(Geometry("MULTIPOLYGON", srid=4326),
                  comment="Límites territoriales oficiales")
