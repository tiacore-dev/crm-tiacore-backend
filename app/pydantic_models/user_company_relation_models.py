from typing import Optional
from pydantic import BaseModel, UUID4, field_validator, Field
from fastapi import Query


class UserCompanyRelationCreateSchema(BaseModel):
    user: UUID4 = Field(...,
                        description="UUID пользователя, связанного с компанией")
    company: UUID4 = Field(..., description="UUID компании")
    role: str = Field(..., min_length=3, max_length=50,
                      description="Роль пользователя в компании")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str):
        """Запрещаем передавать пустые строки в role"""
        if value.strip() == "":
            raise ValueError("Поле role не может быть пустым.")
        return value

    class Config:
        from_attributes = True


class UserCompanyRelationSchema(BaseModel):
    user_company_id: UUID4
    user_id: UUID4
    company_id: UUID4
    role_id: str

    class Config:
        from_attributes = True


class UserCompanyRelationListResponseSchema(BaseModel):
    total: int  # 🔥 Количество связей по фильтру
    # ✅ Используем `list`, а не `List[UserCompanyRelationSchema]`
    relations: list

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


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
