from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


def find_env_file() -> Path | None:
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        env_path = parent / ".env"
        if env_path.exists():
            return env_path
    return None


class Settings(BaseSettings):
    openai_api_key: str = ""
    database_url: str = "sqlite:///./data/app.db"

    model_config = ConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
