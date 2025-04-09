import os
from dotenv import load_dotenv

ENV_FILE = ".env.test" if os.getenv("CI") == "true" else ".env"
load_dotenv(dotenv_path=ENV_FILE)
# Загрузка переменных из .env


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://db.sqlite3")
    TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL', "sqlite://db.sqlite3")
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
    ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS = os.getenv('REFRESH_TOKEN_EXPIRE_DAYS')
    # LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_LEVEL = "DEBUG"
    ALGORITHM = "HS256"
    PORT = os.getenv('PORT')
    ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "").split(",")
    ORIGIN = os.getenv("ORIGIN")
    ENDPOINT_URL = os.getenv('ENDPOINT_URL')
    REGION_NAME = os.getenv('REGION_NAME')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    BUCKET_NAME = os.getenv('BUCKET_NAME')
    OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT")
