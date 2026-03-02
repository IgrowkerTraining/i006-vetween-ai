"""Application settings and configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    app_name: str = "FastAPI AI Template"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # OpenRouter Configuration
    openrouter_api_key: str | None = None
    openrouter_base_url: str | None = None
    # Nvidia Configuration
    nvidia_api_url : str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_key : str
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Agrego la confifuración para acceder a la DB
    # DB configuration
    supabase_url: str = "https://qohfarniqorfuwazhdqj.supabase.co"
    supabase_key: str

    # CORS Configuration
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Logging Configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
