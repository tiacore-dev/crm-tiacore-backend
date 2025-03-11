from .auth_route import auth_router
from .get_route import get_router
from .service_route import service_router
from .user_route import user_router
from .company_route import company_router
from .user_company_relation_route import relation_router
from .legal_entity_route import entity_router

# Функция для регистрации всех маршрутов


def register_routes(app):
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(get_router, prefix="/api/get-all",
                       tags=["Statuses, Types, Roles"])
    app.include_router(
        service_router, prefix="/api/services", tags=["Services"])
    app.include_router(user_router, prefix="/api/users", tags=["Users"])
    app.include_router(
        company_router, prefix="/api/companies", tags=["Companies"])
    app.include_router(
        relation_router, prefix='/api/user-company-relations', tags=["UserCompanyRelations"])
    app.include_router(
        entity_router, prefix='/api/legal-entities', tags=["LegalEntities"])
