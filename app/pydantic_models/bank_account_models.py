from typing import List, Optional
from uuid import UUID

from fastapi import Query
from pydantic import Field
from tiacore_lib.pydantic_models.clean_model import CleanableBaseModel


class BankAccountCreateSchema(CleanableBaseModel):
    number: str = Field(..., min_length=20, max_length=20, alias="account_number")
    bank_name: str = Field(..., min_length=3, max_length=255)
    bank_bic: str = Field(..., min_length=9, max_length=9)
    bank_corr_account: str = Field(..., min_length=20, max_length=20)
    legal_entity_id: UUID = Field(..., alias="legal_entity")

    class Config:
        from_attributes = True
        populate_by_name = True


class BankAccountSchema(CleanableBaseModel):
    bank_account_id: UUID
    legal_entity: UUID
    bank_name: str
    account_number: str
    bank_bic: str
    bank_corr_account: str

    class Config:
        from_attributes = True
        populate_by_name = True


class BankAccountResponseSchema(CleanableBaseModel):
    bank_account_id: UUID

    class Config:
        from_attributes = True


class BankAccountListResponseSchema(CleanableBaseModel):
    total: int

    bank_accounts: List[BankAccountSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class BankAccountEditSchema(CleanableBaseModel):
    number: Optional[str] = Field(
        None, min_length=20, max_length=20, alias="account_number"
    )
    bank_name: Optional[str] = Field(None, min_length=3, max_length=255)
    bank_bic: Optional[str] = Field(None, min_length=9, max_length=9)
    bank_corr_account: Optional[str] = Field(None, min_length=20, max_length=20)
    legal_entity_id: Optional[UUID] = Field(None, alias="legal_entity")

    class Config:
        from_attributes = True


def bank_account_filter_params(
    legal_entity: Optional[UUID] = Query(None, description="Фильтр по юр. лицу"),
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
