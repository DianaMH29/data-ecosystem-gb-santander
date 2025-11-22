"""
Configuración de la aplicación - Carga credenciales desde confiig_santander.yml
"""
import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings


def load_yaml_config():
    """Carga la configuración desde el archivo YAML"""
    # Primero intenta la ruta de Docker (/app/confiig_santander.yml)
    docker_path = Path("/app/confiig_santander.yml")
    if docker_path.exists():
        config_path = docker_path
    else:
        # Ruta local (desarrollo)
        config_path = Path(__file__).parent.parent.parent / "confiig_santander.yml"
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Base de datos
    DB_DRIVER: str = "postgresql+psycopg2"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "santander"
    DB_USER: str = "admin-santander"
    DB_PASSWORD: str = "admin-gob"
    
    # API
    API_TITLE: str = "Atlas al Crimen - Santander API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    @property
    def DATABASE_URL(self) -> str:
        return f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Obtiene la configuración, priorizando el archivo YAML"""
    yaml_config = load_yaml_config()
    db_config = yaml_config.get("database", {})
    
    return Settings(
        DB_DRIVER=db_config.get("driver", "postgresql+psycopg2"),
        DB_HOST=db_config.get("host", "localhost"),
        DB_PORT=db_config.get("port", 5432),
        DB_NAME=db_config.get("db_name", "santander"),
        DB_USER=db_config.get("user", "admin-santander"),
        DB_PASSWORD=db_config.get("password", "admin-gob"),
    )


settings = get_settings()
