"""Configuración central de la API (Plan Maestro §3.1)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_title: str = "LexIAParaguay API central"

    # Orígenes web autorizados, separados por coma (§7.4).
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # PostgreSQL 16 + pgvector
    database_url: str = "postgresql+asyncpg://lexia:lexia@postgres:5432/lexia"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 60 * 60 * 24

    # Firebase Authentication (§7) — se verifica cada ID token; nunca se confía en el UID del cliente.
    firebase_project_id: str | None = None
    firebase_credentials: str | None = None  # ruta al JSON de la cuenta de servicio

    # Modelos de IA (§10, §12)
    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072
    chat_model: str = "gpt-5"
    openai_base_url: str | None = None

    # Firecrawl — motor de investigación documental
    firecrawl_api_key: str | None = None

    # Búsqueda híbrida (§11)
    rag_top_k: int = 10
    bm25_weight: float = 0.4
    vector_weight: float = 0.6

    # ETL (§9)
    chunk_tokens: int = 500
    chunk_overlap_tokens: int = 100
    max_download_bytes: int = 40 * 1024 * 1024

    # Actualización automática (§19)
    update_hour: int = 3
    update_minute: int = 0
    update_timezone: str = "America/Asuncion"

    @property
    def auth_configured(self) -> bool:
        return bool(self.firebase_project_id and self.firebase_credentials)

    @property
    def ai_configured(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
