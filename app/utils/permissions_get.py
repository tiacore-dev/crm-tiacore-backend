from collections import defaultdict
from typing import Dict, List
from uuid import UUID

from fastapi import HTTPException
from loguru import logger

from app.database.models import (
    EntityCompanyRelation,
    LegalEntity,
    RolePermissionRelation,
    User,
    UserCompanyRelation,
)


async def get_company_permissions_for_user(user: User) -> Dict[UUID, List[str]] | None:
    if user.is_superadmin:
        return None

    # 1. Получаем все связи юзера с компаниями и ролями
    relations = await UserCompanyRelation.filter(user=user).select_related(
        "company", "role"
    )

    # 2. Получаем все разрешения по всем ролям сразу
    role_ids = {rel.role.role_id for rel in relations}
    role_to_permissions = defaultdict(list)

    role_permissions = await RolePermissionRelation.filter(
        role_id__in=role_ids
    ).prefetch_related("permission")

    for rp in role_permissions:
        role_to_permissions[str(rp.role_id)].append(rp.permission.permission_id)

    company_permissions: Dict[UUID, List[str]] = {}
    for rel in relations:
        company_id = rel.company.company_id
        role_id = str(rel.role.role_id)
        perms = role_to_permissions.get(role_id, [])
        company_permissions[company_id] = perms

    return company_permissions


async def ensure_seller_belongs_to_company(seller: LegalEntity, company_id: UUID):
    is_seller = await EntityCompanyRelation.exists(
        legal_entity=seller, company_id=company_id, relation_type="seller"
    )
    if not is_seller:
        logger.warning(
            f"Попытка использовать чужого продавца: {seller.legal_entity_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="""Вы не можете действовать от имени юрлица, 
            не связанного с вашей компанией как продавец""",
        )
