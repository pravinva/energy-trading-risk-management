from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    databricks_host: str = 'https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/'
    lakebase_host: str = ''
    lakebase_database: str = ''
    lakebase_port: int = 5432
    nexus_environment: Literal['dev', 'prod'] = 'dev'
    apex_environment: Literal['dev', 'prod'] = 'dev'
    apex_catalog: str = 'apex_fresh'
    app_version: str = '1.0.0'
    cors_origins: list[str] = ['http://localhost:5173']
    nexus_dev_user_email: str | None = None

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
