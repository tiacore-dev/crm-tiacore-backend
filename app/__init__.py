import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_422_UNPROCESSABLE_ENTITY

from prometheus_client import make_asgi_app
from tortoise.contrib.fastapi import register_tortoise
from app.logger import setup_logger
from app.routes import register_routes
from app.config import Settings
# from app.middleware.trace import TraceIDMiddleware
# Определяем OAuth2 (аналогично Flask)


def create_app(config_name) -> FastAPI:
    app = FastAPI(title="CRM")
    setup_logger()
    settings = Settings()
    if config_name == 'Test':
        origin = "*"
        db_url = settings.TEST_DATABASE_URL
    else:
        db_url = settings.DATABASE_URL
        origin = settings.ORIGIN
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin],
        allow_credentials=True,  # Разрешаем использование кук и авторизации
        allow_methods=["*"],
        allow_headers=["*"],  # Разрешаем все заголовки
    )
    # app.add_middleware(TraceIDMiddleware)
    app.mount("/metrics", make_asgi_app())
    if config_name == "Production":
        from app.tracer import init_tracer
        init_tracer(app)

    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": ["app.database.models"]},
        add_exception_handlers=True,
        # Генерация схем только в тестах
        generate_schemas=(config_name == 'Test')
    )
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

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
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        from loguru import logger
        logger.error(f"Unhandled Exception: {traceback.format_exc()}")

        response = JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        from loguru import logger
        logger.error(
            f"Request Validation Error: {exc.errors()} | body: {exc.body}")

        response = JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    return app
