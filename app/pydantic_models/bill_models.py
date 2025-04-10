from typing import Optional, List
from pydantic import UUID4, field_validator, Field, model_validator
from fastapi import Query, HTTPException
from app.pydantic_models.clean_model import CleanableBaseModel


class BillCreateSchema(CleanableBaseModel):
    bank_account: UUID4 = Field(...)
    bill_number: str = Field(..., min_length=3, max_length=255)
    bill_date: int = Field(..., ge=0)  # Unix timestamp
    contract: Optional[UUID4] = Field(None)
    buyer: Optional[UUID4] = Field(None)
    seller: Optional[UUID4] = Field(None)

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

    @model_validator(mode="after")
    def check_contract_or_parties(self) -> 'BillCreateSchema':
        if not self.contract:
            if not self.buyer or not self.seller:
                raise HTTPException(
                    status_code=400,
                    detail="Either 'contract' must be provided, or both 'buyer' and 'seller' must be specified."
                )
        return self

    class Config:
        from_attributes = True


class BillResponseSchema(CleanableBaseModel):
    bill_id: UUID4

    class Config:
        from_attributes = True


class BillEditSchema(CleanableBaseModel):
    bank_account: Optional[UUID4] = None
    bill_number: Optional[str] = None
    bill_date: Optional[int] = None
    contract: Optional[UUID4] = None
    buyer: Optional[UUID4] = None
    seller: Optional[UUID4] = None

    class Config:
        from_attributes = True


class BillSchema(CleanableBaseModel):
    bill_id: UUID4
    bill_number: str
    bill_date: int
    bank_account: UUID4
    contract: Optional[UUID4] = None
    buyer: UUID4
    seller: UUID4

    class Config:
        from_attributes = True


class BillListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Количество записей по фильтру
    bills: List[BillSchema]  # ✅ Используем `list`, а не `List[BillSchema]`

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


def bill_filter_params(
    bank_account: Optional[UUID4] = Query(
        None, description="Фильтр по банковскому счету"),
    contract: Optional[UUID4] = Query(None, description="Фильтр по контракту"),
    bill_date_from: Optional[int] = Query(
        None, description="Фильтр по дате от (timestamp)"),
    bill_date_to: Optional[int] = Query(
        None, description="Фильтр по дате до (timestamp)"),
    sort_by: Optional[str] = Query("bill_date", description="Поле сортировки"),
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "bank_account": bank_account,
        "contract": contract,
        "bill_date_from": bill_date_from,
        "bill_date_to": bill_date_to,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
