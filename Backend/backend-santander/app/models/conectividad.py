"""
Modelo: master_conectividad - Dimensión Tecnológica
"""
from sqlalchemy import Column, Integer, Float, ForeignKey
from ..database import Base


class MasterConectividad(Base):
    """
    Indicadores de brecha digital. Proxy para subregistro de denuncias.
    """
    __tablename__ = "master_conectividad"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_dane = Column(Integer, ForeignKey("master_municipios.codigo_dane"), index=True,
                         comment="FK -> master_municipios")
    cobertura_4g_urbana = Column(Integer, default=0,
                                 comment="Binario (1/0)")
    cobertura_4g_rural = Column(Integer, default=0,
                                comment="Binario (1/0)")
    brecha_digital_idx = Column(Float,
                                comment="Índice de desconexión calculado")
