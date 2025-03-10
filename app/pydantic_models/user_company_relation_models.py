from typing import Optional
from pydantic import BaseModel, UUID4
from fastapi import Query


class UserCompanyRelationCreateSchema(BaseModel):
    user: UUID4
    company: UUID4
    role: str

    class Config:
        from_attributes = True


class UserCompanyRelationResponseSchema(BaseModel):
    user_company_id: UUID4

    class Config:
        from_attributes = True


class UserCompanyRelationEditSchema(BaseModel):
    user: Optional[UUID4] = None
    company: Optional[UUID4] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True


def user_company_filter_params(
    user: Optional[UUID4] = Query(
        None, description="Фильтр по пользователю"),
    company: Optional[UUID4] = Query(
        None, description="Фильтр по компании"),
    role: Optional[str] = Query(None, description="Фильтр по роли"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "user": user,
        "company": company,
        "role": role,
        "page": page,
        "page_size": page_size,
    }
