from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://coffee_user:3004@localhost:5432/cafe"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://coffee_user:3004@localhost:5432/cafe"
    SECRET_KEY: str = "3004"
    DEBUG: bool = True
    WEBHOOK_SECRET: str = "3004"
    PAYMENT_PROVIDER: str
    PAYMENT_PUBLIC_KEY: str
    PAYMENT_SECRET_KEY: str
    PAYMENT_WEBHOOK_SECRET: str
    PAYMENT_WEBHOOK_URL: str


    SENTRY_DSN: str | None = None


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

@lru_cache()
def get_settings() -> Settings:
    return Settings()