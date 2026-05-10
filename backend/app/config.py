from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_publishable_key: str = ""
    frontend_url: str = "http://localhost:3000"
    admin_api_key: str = "demo-admin-key-change-me"


settings = Settings()
