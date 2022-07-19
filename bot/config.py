import os


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///plans.db")
