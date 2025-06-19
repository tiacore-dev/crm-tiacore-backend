from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, Query
from pydantic import Field, field_validator
from tiacore_lib.pydantic_models.clean_model import CleanableBaseModel


class BillDetailCreateSchema(CleanableBaseModel):
    bill: UUID = Field(...)
    service: UUID = Field(...)
    quantity: Decimal = Field(..., gt=0)
    # summ: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0, max_digits=8, decimal_places=2)

    @field_validator("bill", "service", "quantity", "price")
    @classmethod
    def validate_required_fields(cls, value, info):
        """Глобальная валидация обязательных полей с выбросом 400 ошибки"""
        if value in [None, "", " ", 0]:
            raise HTTPException(
                status_code=400,
                detail=f"""Поле {info.field_name} обязательно 
                для заполнения и не может быть пустым или нулевым.""",
            )
        return value

    class Config:
        from_attributes = True
        populate_by_name = True


class BillDetailResponseSchema(CleanableBaseModel):
    bill_detail_id: UUID

    class Config:
        from_attributes = True
        populate_by_name = True


class BillDetailEditSchema(CleanableBaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0)
    # summ: Optional[Decimal] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0)

    class Config:
        from_attributes = True
        populate_by_name = True


class BillDetailSchema(CleanableBaseModel):
    bill_detail_id: UUID
    bill: UUID
    service: UUID
    quantity: Decimal
    summ: Decimal
    price: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class BillDetailListResponseSchema(CleanableBaseModel):
    total: int
    bill_details: List[BillDetailSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


def bill_detail_filter_params(
    bill: Optional[UUID] = Query(None, description="Фильтр по счету"),
    service: Optional[UUID] = Query(None, description="Фильтр по услуге"),
    sort_by: Optional[str] = Query("created_at", description="Поле сортировки"),
    order: Optional[str] = Query("desc", description="Порядок сортировки: asc/desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "bill": bill,
        "service": service,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
