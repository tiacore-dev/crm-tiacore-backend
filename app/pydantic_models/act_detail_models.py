from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, UUID4, field_validator, Field
from fastapi import Query, HTTPException


class ActDetailCreateSchema(BaseModel):
    act: UUID4 = Field(...)
    service: UUID4 = Field(...)
    quantity: Decimal = Field(..., gt=0, max_digits=8, decimal_places=3)
    summ: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)

    @field_validator("act", "service", "quantity", "summ")
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


class ActDetailSchema(BaseModel):
    act_detail_id: UUID4
    act: UUID4  # ✅ Передаем UUID вместо объекта
    service: UUID4  # ✅ Передаем UUID вместо объекта
    quantity: float
    summ: float

    class Config:
        from_attributes = True


class ActDetailResponseSchema(BaseModel):
    act_detail_id: UUID4

    class Config:
        from_attributes = True


class ActDetailListResponseSchema(BaseModel):
    total: int  # 🔥 Общее количество деталей акта по фильтру
    act_details: list  # ✅ Используем `list`, а не `List[ActDetailSchema]`

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class ActDetailEditSchema(BaseModel):
    act: Optional[UUID4] = None
    service: Optional[UUID4] = None
    quantity: Optional[Decimal] = None
    summ: Optional[Decimal] = None

    class Config:
        from_attributes = True


def act_detail_filter_params(
    act: Optional[UUID4] = Query(None, description="Фильтр по акту"),
    service: Optional[UUID4] = Query(None, description="Фильтр по услуге"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "act": act,
        "service": service,
        "page": page,
        "page_size": page_size,
    }
