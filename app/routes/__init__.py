from .auth_route import auth_router
from .get_route import get_router
from .service_route import service_router
from .user_route import user_router
from .company_route import company_router
from .user_company_relation_route import relation_router
from .legal_entity_route import entity_router
from .contract_route import contract_router
from .bank_account_route import bank_account_router
from .act_route import act_router
from .act_detail_route import act_detail_router
from .bill_route import bill_router
from .bill_detail_route import bill_detail_router
from .template_route import template_router
from .easter_route import easter_router
from .role_route import role_router
from .permissions_route import permissions_router
from .role_permission_relation_route import role_relation_router
from .entity_company_relation_route import entity_relation_router
# Функция для регистрации всех маршрутов


def register_routes(app):
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(get_router, prefix="/api",
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
    app.include_router(
        contract_router, prefix='/api/contracts', tags=["Contracts"])
    app.include_router(bank_account_router,
                       prefix='/api/bank-accounts', tags=["BankAccounts"])
    app.include_router(act_router, prefix='/api/acts', tags=["Acts"])
    app.include_router(act_detail_router,
                       prefix='/api/act-details', tags=["ActDetails"])
    app.include_router(bill_router, prefix='/api/bills', tags=["Bills"])
    app.include_router(bill_detail_router,
                       prefix='/api/bill-details', tags=["BillDetails"])
    app.include_router(
        template_router, prefix='/api/templates', tags=["Templates"])
    app.include_router(easter_router)
    app.include_router(role_router, prefix='/api/roles', tags=["Roles"])
    app.include_router(permissions_router,
                       prefix='/api/permissions', tags=["Permissions"])
    app.include_router(role_relation_router,
                       prefix='/api/role-permission-relations', tags=["RolePermissionRelations"])
    app.include_router(entity_relation_router,
                       prefix='/api/entity-company-relations', tags=["EntityCompanyRelations"])
