from uuid import UUID
from fastapi import HTTPException
from app.database.models import User, UserCompanyRelation, Permissions


async def get_user_permissions(username: str, company: UUID) -> list[str]:
    user = await User.get(username=username)

    relation = await UserCompanyRelation.filter(
        user=user, company=company
    ).select_related("role").first()

    if not relation:
        raise HTTPException(
            status_code=403, detail="Нет доступа к указанной компании")

    permissions = await Permissions.filter(
        role_permission_relations__role=relation.role
    ).values_list("permission_id", flat=True)

    return list(permissions)
