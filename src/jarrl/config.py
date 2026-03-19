import os


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./data/jarrl.sqlite")


def get_feed_base_url() -> str:
    return os.getenv("FEED_BASE_URL", "http://localhost:8000/rss")


def get_api_base_url() -> str:
    return os.getenv("API_BASE_URL", "http://api:8000")


def get_bot_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is required")
    return token


def get_allowed_telegram_user_id() -> int:
    value = os.getenv("ALLOWED_TELEGRAM_USER_ID")
    if not value:
        raise RuntimeError("ALLOWED_TELEGRAM_USER_ID is required")
    return int(value)
