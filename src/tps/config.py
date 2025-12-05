"""Configuration management for TPS"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # API Keys
    deepl_api_key: Optional[str] = Field(default=None, alias="DEEPL_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    google_application_credentials: Optional[str] = Field(
        default=None, alias="GOOGLE_APPLICATION_CREDENTIALS"
    )
    google_cloud_project: Optional[str] = Field(
        default=None, alias="GOOGLE_CLOUD_PROJECT"
    )
    
    # Database
    sqlite_db_path: str = Field(default="./data/tps.db", alias="SQLITE_DB_PATH")
    
    # Budget Limits (USD per day)
    daily_budget_google: float = Field(default=10.0, alias="DAILY_BUDGET_GOOGLE")
    daily_budget_openai: float = Field(default=5.0, alias="DAILY_BUDGET_OPENAI")
    
    # Server Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # OpenAI Model Settings
    openai_translation_model: str = "gpt-4o-mini"
    openai_refinement_model: str = "gpt-4o-mini"
    
    # Pricing (per 1M tokens/chars)
    openai_price_input: float = 0.15  # gpt-4o-mini input
    openai_price_output: float = 0.60  # gpt-4o-mini output
    google_price_per_million_chars: float = 20.0
    
    # Cache settings
    cache_expire_days: int = 90
    
    @property
    def db_path(self) -> Path:
        """Get database path as Path object, creating parent directories if needed"""
        path = Path(self.sqlite_db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
settings = Settings()
