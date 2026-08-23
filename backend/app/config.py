from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    app_name: str = "Personalized Learning AI"
    debug: bool = True
    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    ollama_model: str = "qwen3:8b"
    google_model : str = "gemini-3.6-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()