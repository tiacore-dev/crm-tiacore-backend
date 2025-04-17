from typing import Dict, List
from collections import defaultdict
from app.database.models import User, UserCompanyRelation, RolePermissionRelation


async def get_company_permissions_for_user(user: User) -> Dict[str, List[str]]:
    if user.is_superadmin:
        # 💎 Достаточно одного универсального маркера
        return {"*": ["*"]}

    # 1. Получаем все связи юзера с компаниями и ролями
    relations = await UserCompanyRelation.filter(user=user).select_related("company", "role")

    # 2. Получаем все разрешения по всем ролям сразу
    role_ids = {rel.role.role_id for rel in relations}
    role_to_permissions = defaultdict(list)

    role_permissions = await RolePermissionRelation.filter(
        role_id__in=role_ids
    ).prefetch_related("permission")

    for rp in role_permissions:
        role_to_permissions[str(rp.role_id)].append(
            rp.permission.permission_id)

    # 3. Собираем мапу: company_id -> permissions
    company_permissions: Dict[str, List[str]] = {}
    for rel in relations:
        company_id = str(rel.company.company_id)
        role_id = str(rel.role.role_id)
        perms = role_to_permissions.get(role_id, [])
        company_permissions[company_id] = perms

    return company_permissions
