"""
Utilidades compartidas para los routers
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from .models import MasterMunicipios


def resolver_municipio(db: Session, municipio: Optional[str]) -> Optional[int]:
    """
    Convierte nombre de municipio a codigo_dane.
    Busqueda case-insensitive y con coincidencia parcial.
    Retorna None si no se especifica municipio.
    """
    if not municipio:
        return None
    
    # Buscar coincidencia exacta (case-insensitive)
    result = db.query(MasterMunicipios.codigo_dane).filter(
        func.upper(MasterMunicipios.nombre_municipio) == municipio.upper()
    ).first()
    
    if result:
        return result.codigo_dane
    
    # Buscar coincidencia parcial (LIKE)
    result = db.query(MasterMunicipios.codigo_dane).filter(
        func.upper(MasterMunicipios.nombre_municipio).like(f"%{municipio.upper()}%")
    ).first()
    
    if result:
        return result.codigo_dane
    
    return None


def get_municipios_lista(db: Session):
    """
    Retorna lista de municipios para selectores.
    """
    results = db.query(
        MasterMunicipios.codigo_dane,
        MasterMunicipios.nombre_municipio,
        MasterMunicipios.categoria_rural_urbana
    ).order_by(MasterMunicipios.nombre_municipio).all()
    
    return [
        {
            "codigo_dane": r.codigo_dane,
            "nombre": r.nombre_municipio,
            "categoria": r.categoria_rural_urbana
        }
        for r in results
    ]
