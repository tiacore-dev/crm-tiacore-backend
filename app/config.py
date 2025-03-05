import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://db.sqlite3")
    TEST_DATABASE_URL = os.getenv('TEST_DB')
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
    ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS = os.getenv('REFRESH_TOKEN_EXPIRE_DAYS')
    # LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_LEVEL = "DEBUG"
    ALGORITHM = "HS256"
    PORT = os.getenv('PORT')
