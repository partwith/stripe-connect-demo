from app.config import settings


def test_settings_load():
    assert settings.database_url.startswith("postgresql")
    assert settings.stripe_secret_key.startswith("sk_")
    assert settings.redis_url.startswith("redis://")
