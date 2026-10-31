from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Report Intelligence Assistant"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/report_intelligence"
    qdrant_url: str = "http://localhost:6333"
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    upload_dir: str = "data/uploads"
    max_upload_mb: int = 100
    seed_sample_documents: bool = False
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
