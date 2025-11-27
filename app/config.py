import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/newsletter")
    STATIC_DIR: str = os.getenv("STATIC_DIR", "static")
    WORDCLOUD_DIR: str = os.getenv("WORDCLOUD_DIR", "static/wordclouds")
    TFIDF_MAX_FEATURES: int = int(os.getenv("TFIDF_MAX_FEATURES", "2000"))

settings = Settings()
