import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///plans.db")
PORT = int(os.getenv("PORT", 5000))

# Logging
USE_LOKI_LOGGER = bool(os.getenv("USE_LOKI_LOGGER", False))
LOKI_URL = os.getenv("LOKI_URL", "")
LOKI_AUTH_LOGIN = os.getenv("LOKI_AUTH_LOGIN", "")
LOKI_AUTH_PASSWORD = os.getenv("LOKI_AUTH_PASSWORD", "")
