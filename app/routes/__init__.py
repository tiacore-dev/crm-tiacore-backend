from .auth_route import auth_router
from .get_route import get_router

# Функция для регистрации всех маршрутов


def register_routes(app):
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(get_router, prefix="/api/get-all",
                       tags=["Statuses, Types, Roles"])
