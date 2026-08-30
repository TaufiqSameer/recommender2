from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    app_name: str = "LearnAI"
    debug: bool = True
    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    ollama_model: str = "qwen3:8b"
    google_model: str = "gemini-2.5-flash"

    # JWT
    jwt_secret: str = "changeme-in-production-use-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()