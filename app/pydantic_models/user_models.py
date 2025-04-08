from typing import Optional, List
from pydantic import Field,  UUID4
from fastapi import Query
from app.pydantic_models.clean_model import CleanableBaseModel


class UserCreateSchema(CleanableBaseModel):
    username: str = Field(..., min_length=3, max_length=50,
                          description="Уникальное имя пользователя")
    password: str = Field(..., min_length=6,
                          description="Пароль (не менее 6 символов)")
    full_name: str = Field(..., min_length=3, max_length=100,
                           description="Полное имя пользователя")
    position: Optional[str] = Field(
        None, max_length=50, description="Должность пользователя")

    class Config:
        from_attributes = True


class UserEditSchema(CleanableBaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    position: Optional[str] = Field(None, max_length=50)


class UserSchema(CleanableBaseModel):
    user_id: UUID4
    username: str
    full_name: str
    position: str


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
    sort_by: Optional[str] = Query("username", description="Поле сортировки"),
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc"),
    page: Optional[int] = Query(1, ge=1, description="Номер страницы"),
    page_size: Optional[int] = Query(
        10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "search": search,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
