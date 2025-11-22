"""
Modelo: fact_incautaciones - Tabla de Hechos (Control)
"""
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from ..database import Base


class FactIncautaciones(Base):
    """
    Operatividad contra el narcotráfico.
    """
    __tablename__ = "fact_incautaciones"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_dane = Column(Integer, ForeignKey("master_municipios.codigo_dane"), index=True,
                         comment="FK -> master_municipios")
    fecha = Column(Date, index=True,
                   comment="Fecha de incautación")
    tipo_droga = Column(String,
                        comment="Sustancia: Marihuana, Cocaína, etc.")
    cantidad_gramos = Column(Float,
                             comment="Peso neto incautado")
