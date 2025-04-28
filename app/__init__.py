from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from prometheus_client import make_asgi_app
from tortoise.contrib.fastapi import register_tortoise
from app.logger import setup_logger
from app.routes import register_routes
from app.config import Settings
# from app.middleware.trace import TraceIDMiddleware
# Определяем OAuth2 (аналогично Flask)


def create_app(config_name) -> FastAPI:
    app = FastAPI(title="CRM")
    settings = Settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"{settings.ORIGIN}"],
        allow_credentials=True,  # Разрешаем использование кук и авторизации
        allow_methods=["*"],
        allow_headers=["*"],  # Разрешаем все заголовки
    )
    # app.add_middleware(TraceIDMiddleware)
    app.mount("/metrics", make_asgi_app())
    if config_name == "Production":
        from app.tracer import init_tracer
        init_tracer(app)

    if config_name == 'Test':
        db_url = settings.TEST_DATABASE_URL
    else:
        db_url = settings.DATABASE_URL
    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": ["app.database.models"]},
        add_exception_handlers=True,
        # Генерация схем только в тестах
        generate_schemas=(config_name == 'Test')
    )
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    setup_logger()
    register_routes(app)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        from loguru import logger
        logger.error(f"Ошибка валидации запроса: {exc}")
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},
        )

    return app
