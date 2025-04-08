from decimal import Decimal
from typing import Optional, List
from pydantic import UUID4, Field, field_validator
from fastapi import Query, HTTPException
from app.pydantic_models.clean_model import CleanableBaseModel


class BillDetailCreateSchema(CleanableBaseModel):
    bill: UUID4 = Field(...)
    service: UUID4 = Field(...)
    quantity: Decimal = Field(..., gt=0)
    summ: Decimal = Field(..., gt=0)

    @field_validator("bill", "service", "quantity", "summ")
    @classmethod
    def validate_required_fields(cls, value, info):
        """Глобальная валидация обязательных полей с выбросом 400 ошибки"""
        if value in [None, "", " ", 0]:
            raise HTTPException(
                status_code=400,
                detail=f"Поле {info.field_name} обязательно для заполнения и не может быть пустым или нулевым.",
            )
        return value

    class Config:
        from_attributes = True


class BillDetailResponseSchema(CleanableBaseModel):
    bill_detail_id: UUID4

    class Config:
        from_attributes = True


class BillDetailEditSchema(CleanableBaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0)
    summ: Optional[Decimal] = Field(None, gt=0)

    class Config:
        from_attributes = True


class BillDetailSchema(CleanableBaseModel):
    bill_detail_id: UUID4
    bill: UUID4  # ✅ Теперь передаем UUID счета
    service: UUID4  # ✅ Теперь передаем UUID услуги
    quantity: Decimal
    summ: Decimal

    class Config:
        from_attributes = True


class BillDetailListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Количество записей по фильтру
    # ✅ Используем `list`, а не `List[BillDetailSchema]`
    bill_details: List[BillDetailSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


def bill_detail_filter_params(
    bill: Optional[UUID4] = Query(None, description="Фильтр по счету"),
    service: Optional[UUID4] = Query(None, description="Фильтр по услуге"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "bill": bill,
        "service": service,
        "page": page,
        "page_size": page_size,
    }
