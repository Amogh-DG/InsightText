import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "storage" / "insighttext.db").as_posix()
DEFAULT_STORAGE_DIR = (BASE_DIR / "storage").as_posix()
DEFAULT_MODEL_DIR = (BASE_DIR / "storage" / "models").as_posix()
DEFAULT_DATASET_DIR = (BASE_DIR / "storage" / "datasets").as_posix()

class Settings(BaseSettings):
    PROJECT_NAME: str = "InsightText"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    SECRET_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    STORAGE_DIR: str = DEFAULT_STORAGE_DIR
    MODEL_STORAGE_DIR: str = DEFAULT_MODEL_DIR
    DATASET_STORAGE_DIR: str = DEFAULT_DATASET_DIR
    CONFIDENCE_THRESHOLD: float = 0.6
    INTENT_LABELS: list[str] = ["complaint", "inquiry", "praise", "request", "suggestion", "other"]
    TARGET_F1: float = 0.85
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.MODEL_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.DATASET_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
