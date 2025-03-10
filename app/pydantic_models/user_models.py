from typing import Optional
from pydantic import BaseModel, Field
from fastapi import Query


class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=3, max_length=100)
    position: Optional[str] = Field(None, max_length=50)


class UserEditSchema(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    position: Optional[str] = Field(None, max_length=50)


class UserResponseSchema(BaseModel):
    user_id: str


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
