from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/taskmanager"

    # Security
    secret_key: str = "your-secret-key-change-this"
    access_token_expire_hours: int = 168  # 7 days

    # App
    app_name: str = "Cronix"
    app_port: int = 8000
    app_debug: bool = False


settings = Settings()
