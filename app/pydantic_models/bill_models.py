from typing import Optional
from pydantic import BaseModel, UUID4, field_validator, Field
from fastapi import Query, HTTPException


class BillCreateSchema(BaseModel):
    bank_account: UUID4 = Field(...)
    bill_number: str = Field(..., min_length=3, max_length=255)
    bill_date: int = Field(..., ge=0)  # Unix timestamp
    contract: UUID4 = Field(...)

    @field_validator("bank_account", "bill_number", "bill_date", "contract")
    @classmethod
    def validate_required_fields(cls, value: str, info):
        """Глобальная валидация обязательных полей с выбросом 400 ошибки"""
        if value in [None, "", " "]:
            raise HTTPException(
                status_code=400,
                detail=f"Поле {info.field_name} обязательно для заполнения.",
            )
        return value

    class Config:
        from_attributes = True


class BillResponseSchema(BaseModel):
    bill_id: UUID4

    class Config:
        from_attributes = True


class BillListResponseSchema(BaseModel):
    total: int  # 🔥 Количество записей по фильтру
    bills: list  # ✅ Используем `list`, а не `List[BillSchema]`

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class BillEditSchema(BaseModel):
    bank_account: Optional[UUID4] = None
    bill_number: Optional[str] = None
    bill_date: Optional[int] = None
    contract: Optional[UUID4] = None

    class Config:
        from_attributes = True


class BillSchema(BaseModel):
    bill_id: UUID4
    bill_number: str
    bill_date: int
    contract: UUID4  # ✅ Теперь это просто UUID
    bank_account: UUID4  # ✅ Теперь это просто UUID

    class Config:
        from_attributes = True


def bill_filter_params(
    bank_account: Optional[UUID4] = Query(
        None, description="Фильтр по банковскому счету"),
    contract: Optional[UUID4] = Query(None, description="Фильтр по контракту"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "bank_account": bank_account,
        "contract": contract,
        "page": page,
        "page_size": page_size,
    }
