from typing import List, Optional

from fastapi import HTTPException, Query
from pydantic import UUID4, Field, field_validator

from app.pydantic_models.clean_model import CleanableBaseModel


class BankAccountCreateSchema(CleanableBaseModel):
    account_number: str = Field(..., min_length=20, max_length=20)
    bank_name: str = Field(..., min_length=3, max_length=255)
    bank_bic: str = Field(..., min_length=9, max_length=9)
    bank_corr_account: str = Field(..., min_length=20, max_length=20)
    legal_entity: UUID4 = Field(...)

    @field_validator(
        "account_number", "bank_name", "bank_bic", "bank_corr_account", "legal_entity"
    )
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


class BankAccountSchema(CleanableBaseModel):
    bank_account_id: UUID4
    legal_entity: UUID4
    bank_name: str
    account_number: str
    bank_bic: str
    bank_corr_account: str

    class Config:
        from_attributes = True


class BankAccountResponseSchema(CleanableBaseModel):
    bank_account_id: UUID4

    class Config:
        from_attributes = True


class BankAccountListResponseSchema(CleanableBaseModel):
    total: int

    bank_accounts: List[BankAccountSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class BankAccountEditSchema(CleanableBaseModel):
    account_number: Optional[str] = Field(None, min_length=20, max_length=20)
    bank_name: Optional[str] = Field(None, min_length=3, max_length=255)
    bank_bic: Optional[str] = Field(None, min_length=9, max_length=9)
    bank_corr_account: Optional[str] = Field(None, min_length=20, max_length=20)
    legal_entity: Optional[UUID4] = None

    class Config:
        from_attributes = True


def bank_account_filter_params(
    legal_entity: Optional[UUID4] = Query(None, description="Фильтр по юр. лицу"),
    bank_name: Optional[str] = Query(None, description="Фильтр по названию банка"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "legal_entity": legal_entity,
        "bank_name": bank_name,
        "page": page,
        "page_size": page_size,
    }
