from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="HDIS Backend", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_cors_origins: str = Field(default="*", alias="APP_CORS_ORIGINS")

    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_db_url: str = Field(default="", alias="SUPABASE_DB_URL")

    jwt_jwks_url: str = Field(default="", alias="JWT_JWKS_URL")
    jwt_audience: str = Field(default="", alias="JWT_AUDIENCE")
    jwt_issuer: str = Field(default="", alias="JWT_ISSUER")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_model_intent: str = Field(default="", alias="LLM_MODEL_INTENT")
    llm_model_risk: str = Field(default="", alias="LLM_MODEL_RISK")
    llm_model_assumption: str = Field(default="", alias="LLM_MODEL_ASSUMPTION")
    llm_model_interview: str = Field(default="", alias="LLM_MODEL_INTERVIEW")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_timeout_seconds: float = Field(default=30.0, alias="LLM_TIMEOUT_SECONDS")

    breaker_error_threshold: int = Field(default=5, alias="BREAKER_ERROR_THRESHOLD")
    breaker_window_seconds: int = Field(default=60, alias="BREAKER_WINDOW_SECONDS")
    breaker_cooldown_seconds: int = Field(default=120, alias="BREAKER_COOLDOWN_SECONDS")

    run_rate_limit_per_minute: int = Field(default=30, alias="RUN_RATE_LIMIT_PER_MINUTE")

    @property
    def cors_origins(self) -> list[str]:
        if not self.app_cors_origins.strip():
            return []
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
