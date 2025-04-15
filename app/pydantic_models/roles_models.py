from typing import Optional, List
from uuid import UUID
from pydantic import Field
from fastapi import Query
from app.pydantic_models.clean_model import CleanableBaseModel


class UserRoleCreateSchema(CleanableBaseModel):
    role_name: str = Field(...)

    class Config:
        from_attributes = True


class UserRoleSchema(CleanableBaseModel):
    role_id: UUID
    role_name: str

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
