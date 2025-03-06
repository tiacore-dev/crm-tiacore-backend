from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from tortoise.contrib.fastapi import register_tortoise
from app.logger import setup_logger
from app.routes import register_routes
from app.config import Settings

# Определяем OAuth2 (аналогично Flask)


def create_app(config_name='Development') -> FastAPI:
    app = FastAPI()

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Или указать твой Netlify-домен
        allow_credentials=True,
        # Разрешаем все методы (POST, GET, OPTIONS и т.д.)
        allow_methods=["*"],
        allow_headers=["*"],  # Разрешаем все заголовки
    )

    @app.middleware("http")
    async def redirect_https(request: Request, call_next):
        """Принудительное перенаправление HTTP → HTTPS"""
        if request.headers.get("x-forwarded-proto", "http") == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url)
        return await call_next(request)

    # Подключаем конфигурацию
    settings = Settings()
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
