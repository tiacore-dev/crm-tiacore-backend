from typing import Dict, List
from app.database.models import User, UserCompanyRelation, Permissions


async def get_company_permissions_for_user(user: User) -> Dict[str, List[str]]:
    if user.is_superadmin:
        return {"*": ["*"]}  # 💥 вот так правильно

    relations = await UserCompanyRelation.filter(user=user).select_related("company", "role")
    company_permissions = {}

    for rel in relations:
        perms = await Permissions.filter(
            role_permission_relations__role=rel.role
        ).values_list("permission_id", flat=True)

        company_permissions[str(rel.company.company_id)] = list(perms)

    return company_permissions
