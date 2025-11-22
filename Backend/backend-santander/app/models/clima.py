"""
Modelo: fact_clima - Tabla de Hechos (Variable Exógena)
"""
from sqlalchemy import Column, Integer, Date, Float, ForeignKey
from ..database import Base


class FactClima(Base):
    """
    Precipitación diaria para correlación ambiental.
    """
    __tablename__ = "fact_clima"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_dane = Column(Integer, ForeignKey("master_municipios.codigo_dane"), index=True,
                         comment="FK -> master_municipios")
    fecha = Column(Date, index=True,
                   comment="Fecha de medición")
    precipitacion_mm = Column(Float, default=0,
                              comment="Milímetros de lluvia (0 = Seco)")
