from typing import List, Optional

from fastapi import Query
from pydantic import UUID4, Field

from app.pydantic_models.clean_model import CleanableBaseModel


class UserCreateSchema(CleanableBaseModel):
    email: str = Field(
        ..., min_length=3, max_length=50, description="Уникальное имя пользователя"
    )
    password: str = Field(..., min_length=6, description="Пароль (не менее 6 символов)")
    full_name: str = Field(
        ..., min_length=3, max_length=100, description="Полное имя пользователя"
    )
    position: Optional[str] = Field(
        None, max_length=50, description="Должность пользователя"
    )
    company: UUID4 = Field(...)

    class Config:
        from_attributes = True


class UserEditSchema(CleanableBaseModel):
    email: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    position: Optional[str] = Field(None, max_length=50)
    is_verified: Optional[bool] = Field(None)


class UserSchema(CleanableBaseModel):
    user_id: UUID4
    email: str
    full_name: str
    position: Optional[str] = None


class UserListResponseSchema(CleanableBaseModel):
    total: int  # Общее количество пользователей по фильтру
    users: List[UserSchema]  # Используем `list`, а не `List[UserSchema]`

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # 🔥 Это разрешает "нестандартные" типы


class UserResponseSchema(CleanableBaseModel):
    user_id: UUID4


def user_filter_params(
    search: Optional[str] = Query(None, description="Фильтр по названию"),
    company: Optional[UUID4] = Query(None, description="Фильтр по компании"),
    sort_by: Optional[str] = Query("email", description="Поле сортировки"),
    order: Optional[str] = Query("asc", description="Порядок сортировки: asc/desc"),
    page: Optional[int] = Query(1, ge=1, description="Номер страницы"),
    page_size: Optional[int] = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "search": search,
        "company": company,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
