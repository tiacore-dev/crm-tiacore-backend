from typing import List, Optional

from fastapi import Query

from app.pydantic_models.clean_model import CleanableBaseModel


class PermissionsSchema(CleanableBaseModel):
    permission_id: str
    permission_name: str
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class PermissionsListResponseSchema(CleanableBaseModel):
    total: int
    permissions: List[PermissionsSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class PermissionsResponseSchema(CleanableBaseModel):
    permission_id: str

    class Config:
        from_attributes = True


def permission_filter_params(
    permission_name: Optional[str] = Query(None, description="Фильтр по названию"),
    comment: Optional[str] = Query(None, description="Комментарий к разрешению"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "permission_name": permission_name,
        "comment": comment,
        "page": page,
        "page_size": page_size,
    }
