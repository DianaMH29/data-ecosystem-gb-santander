"""
Modelo: master_frentes_seguridad - Dimensión Social
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from ..database import Base


class MasterFrentesSeguridad(Base):
    """
    Organización comunitaria y capital social.
    """
    __tablename__ = "master_frentes_seguridad"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_dane = Column(Integer, ForeignKey("master_municipios.codigo_dane"), index=True,
                         comment="FK -> master_municipios")
    nombre_frente = Column(String,
                           comment="Barrio o vereda del frente")
    nro_integrantes = Column(Integer,
                             comment="Cantidad de ciudadanos activos")
    estado = Column(String,
                    comment="Estado operativo del frente")
