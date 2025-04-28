from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

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
        allow_origins=[settings.ORIGIN],
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

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        from loguru import logger
        logger.error(
            f"HTTPException: {exc.status_code} - {exc.detail} на {request.url}")

        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
        # Принудительно вставляем CORS заголовки
        response.headers["Access-Control-Allow-Origin"] = settings.ORIGIN
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    return app
