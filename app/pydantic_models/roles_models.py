from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import Field

from app.pydantic_models.clean_model import CleanableBaseModel


class UserRoleCreateSchema(CleanableBaseModel):
    role_name: str = Field(...)

    class Config:
        from_attributes = True


class UserRoleCreateManySchema(CleanableBaseModel):
    role_name: str = Field(...)
    permissions: List[str] = Field(
        ..., description="Список ID разрешений, которые будут назначены этой роли"
    )

    class Config:
        from_attributes = True


class UserRoleSchema(CleanableBaseModel):
    role_id: UUID
    role_name: str
    role_system_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserRoleListResponseSchema(CleanableBaseModel):
    total: int
    roles: List[UserRoleSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class UserRoleResponseSchema(CleanableBaseModel):
    role_id: UUID

    class Config:
        from_attributes = True


class UserRoleEditSchema(CleanableBaseModel):
    role_name: Optional[str] = None

    class Config:
        from_attributes = True


def role_filter_params(
    role_name: Optional[str] = Query(None, description="Фильтр по роли"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "role_name": role_name,
        "page": page,
        "page_size": page_size,
    }
