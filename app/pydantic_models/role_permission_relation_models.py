from uuid import UUID
from typing import Optional, List
from fastapi import Query
from pydantic import Field
from app.pydantic_models.clean_model import CleanableBaseModel


class RolePermissionRelationCreateSchema(CleanableBaseModel):
    role: UUID = Field(..., description="ID роли")
    permission: str = Field(..., description="ID разрешения")

    class Config:
        from_attributes = True


class RolePermissionRelationEditSchema(CleanableBaseModel):
    role: Optional[UUID] = Field(None, description="Новый ID роли")
    permission: Optional[str] = Field(None, description="Новый ID разрешения")

    class Config:
        from_attributes = True


class RolePermissionRelationSchema(CleanableBaseModel):
    role_permission_id: UUID
    role_id: UUID
    permission_id: str

    class Config:
        from_attributes = True


class RolePermissionRelationResponseSchema(CleanableBaseModel):
    role_permission_id: UUID

    class Config:
        from_attributes = True


class RolePermissionRelationListResponseSchema(CleanableBaseModel):
    total: int
    relations: List[RolePermissionRelationSchema]

    class Config:
        from_attributes = True


def role_permission_filter_params(
    role: Optional[UUID] = Query(None, description="Фильтр по роли"),
    permission: Optional[str] = Query(
        None, description="Фильтр по разрешению"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "role": role,
        "permission": permission,
        "page": page,
        "page_size": page_size,
    }
