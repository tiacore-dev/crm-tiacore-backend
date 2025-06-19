from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import Field
from tiacore_lib.pydantic_models.clean_model import CleanableBaseModel


class ActDetailCreateSchema(CleanableBaseModel):
    act: UUID = Field(...)
    service: UUID = Field(...)
    quantity: Decimal = Field(..., gt=0, max_digits=8, decimal_places=3)
    # summ: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    price: Decimal = Field(..., gt=0, max_digits=8, decimal_places=2)

    class Config:
        from_attributes = True


class ActDetailSchema(CleanableBaseModel):
    act_detail_id: UUID
    act: UUID  # ✅ Передаем UUID вместо объекта
    service: UUID  # ✅ Передаем UUID вместо объекта
    quantity: Decimal
    summ: Decimal
    price: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class ActDetailResponseSchema(CleanableBaseModel):
    act_detail_id: UUID

    class Config:
        from_attributes = True


class ActDetailListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Общее количество деталей акта по фильтру
    # ✅ Используем `list`, а не `List[ActDetailSchema]`
    act_details: List[ActDetailSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class ActDetailEditSchema(CleanableBaseModel):
    act: Optional[UUID] = None
    service: Optional[UUID] = None
    quantity: Optional[Decimal] = None
    summ: Optional[Decimal] = None
    price: Optional[Decimal] = None

    class Config:
        from_attributes = True


def act_detail_filter_params(
    act: Optional[UUID] = Query(None, description="Фильтр по акту"),
    service: Optional[UUID] = Query(None, description="Фильтр по услуге"),
    sort_by: Optional[str] = Query("created_at", description="Поле сортировки"),
    order: Optional[str] = Query("desc", description="Порядок сортировки: asc/desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "act": act,
        "service": service,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
