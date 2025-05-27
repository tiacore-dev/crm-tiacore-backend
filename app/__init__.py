from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app
from tortoise.contrib.fastapi import register_tortoise

from app.config import Settings
from app.logger import setup_logger
from app.routes import register_routes


def create_app(config_name) -> FastAPI:
    app = FastAPI(title="CRM")
    setup_logger()
    settings = Settings()
    if config_name == "Test":
        db_url = settings.TEST_DATABASE_URL
    elif config_name == "Development":
        db_url = settings.DOCKER_DATABASE_URL
    else:
        db_url = settings.DATABASE_URL
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/metrics", make_asgi_app())
    if config_name == "Production":
        from app.tracer import init_tracer

        init_tracer(app)

    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": ["app.database.models"]},
        add_exception_handlers=True,
        generate_schemas=(config_name == "Test"),
    )
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    register_routes(app)

    return app
