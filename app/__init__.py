from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from tortoise.contrib.fastapi import register_tortoise
from app.logger import setup_logger
from app.routes import register_routes
from app.config import Settings

# Определяем OAuth2 (аналогично Flask)


def create_app(config_name='Development') -> FastAPI:
    app = FastAPI()
    settings = Settings()
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    # allow_origins = settings.ALLOW_ORIGINS
    # dynamic_local_origins = [
    #     f"http://192.168.1.{i}:3000" for i in range(1, 255)]
    # allow_origins.extend(dynamic_local_origins)

    app.add_middleware(
        CORSMiddleware,
        # allow_origins=allow_origins,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем конфигурацию

    if config_name == 'Test':
        db_url = settings.TEST_DATABASE_URL
    else:
        db_url = settings.DATABASE_URL
    # Настройка базы для тестов/разработки/прода
    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": ["app.database.models"]},
        add_exception_handlers=True,
        # Генерация схем только в тестах
        generate_schemas=(config_name == 'Test')
    )

    setup_logger()
    register_routes(app)

    return app
