from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import UUID4, field_validator, Field
from fastapi import Query, HTTPException
from app.pydantic_models.clean_model import CleanableBaseModel


class ActDetailCreateSchema(CleanableBaseModel):
    act: UUID4 = Field(...)
    service: UUID4 = Field(...)
    quantity: Decimal = Field(..., gt=0, max_digits=8, decimal_places=3)
    # summ: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    price: Decimal = Field(..., gt=0, max_digits=8, decimal_places=2)

    @field_validator("act", "service", "quantity", "price")
    @classmethod
    def validate_required_fields(cls, value, info):
        """Глобальная валидация обязательных полей с выбросом 400 ошибки"""
        if value in [None, "", " "]:
            raise HTTPException(
                status_code=400,
                detail=f"Поле {info.field_name} обязательно для заполнения.",
            )
        return value

    class Config:
        from_attributes = True


class ActDetailSchema(CleanableBaseModel):
    act_detail_id: UUID4
    act: UUID4  # ✅ Передаем UUID вместо объекта
    service: UUID4  # ✅ Передаем UUID вместо объекта
    quantity: float
    summ: float
    price: float
    created_at: datetime

    class Config:
        from_attributes = True


class ActDetailResponseSchema(CleanableBaseModel):
    act_detail_id: UUID4

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
    act: Optional[UUID4] = None
    service: Optional[UUID4] = None
    quantity: Optional[Decimal] = None
    summ: Optional[Decimal] = None
    price: Optional[Decimal] = None

    class Config:
        from_attributes = True


def act_detail_filter_params(
    act: Optional[UUID4] = Query(None, description="Фильтр по акту"),
    service: Optional[UUID4] = Query(None, description="Фильтр по услуге"),
    sort_by: Optional[str] = Query(
        "created_at", description="Поле сортировки"),
    order: Optional[str] = Query(
        "desc", description="Порядок сортировки: asc/desc"),
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
