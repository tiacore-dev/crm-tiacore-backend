from fastapi import FastAPI
from tiacore_lib.routes.auth_route import auth_router
from tiacore_lib.routes.company_route import company_router
from tiacore_lib.routes.invite_route import invite_router
from tiacore_lib.routes.register_route import register_router
from tiacore_lib.routes.role_route import role_router
from tiacore_lib.routes.user_route import user_router

from .act_detail_route import act_detail_router
from .act_route import act_router
from .bank_account_route import bank_account_router
from .bill_detail_route import bill_detail_router
from .bill_route import bill_router
from .contract_route import contract_router
from .easter_route import easter_router
from .get_route import get_router
from .legal_entity_route import entity_router
from .service_route import service_router
from .template_route import template_router


def register_routes(app: FastAPI):
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(invite_router, prefix="/api", tags=["Invite"])
    app.include_router(register_router, prefix="/api", tags=["Register"])
    app.include_router(user_router, prefix="/api/users", tags=["Users"])
    app.include_router(company_router, prefix="/api/companies", tags=["Companies"])
    app.include_router(role_router, prefix="/api/roles", tags=["Roles"])

    app.include_router(get_router, prefix="/api", tags=["Statuses"])
    app.include_router(service_router, prefix="/api/services", tags=["Services"])

    app.include_router(contract_router, prefix="/api/contracts", tags=["Contracts"])
    app.include_router(
        bank_account_router, prefix="/api/bank-accounts", tags=["BankAccounts"]
    )
    app.include_router(act_router, prefix="/api/acts", tags=["Acts"])
    app.include_router(
        act_detail_router, prefix="/api/act-details", tags=["ActDetails"]
    )
    app.include_router(bill_router, prefix="/api/bills", tags=["Bills"])
    app.include_router(
        bill_detail_router, prefix="/api/bill-details", tags=["BillDetails"]
    )
    app.include_router(template_router, prefix="/api/templates", tags=["Templates"])
    app.include_router(easter_router)
    app.include_router(
        entity_router, prefix="/api/legal-entities", tags=["LegalEntities"]
    )
