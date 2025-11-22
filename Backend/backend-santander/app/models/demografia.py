"""
Modelo: master_demografia - Dimensión Contextual
"""
from sqlalchemy import Column, Integer, ForeignKey
from ..database import Base


class MasterDemografia(Base):
    """
    Datos poblacionales para normalización de tasas (Crime Rate).
    """
    __tablename__ = "master_demografia"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_dane = Column(Integer, ForeignKey("master_municipios.codigo_dane"), index=True,
                         comment="FK -> master_municipios")
    anio = Column(Integer, nullable=False,
                  comment="Año de la proyección censal")
    poblacion_total = Column(Integer,
                             comment="Denominador para tasas por 100.000 hab")
    poblacion_rural = Column(Integer,
                             comment="Población dispersa")
    poblacion_cabecera = Column(Integer,
                                comment="Población en casco urbano")
