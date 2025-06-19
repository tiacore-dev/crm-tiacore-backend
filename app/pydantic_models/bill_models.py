from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, Query
from pydantic import Field, model_validator
from tiacore_lib.pydantic_models.clean_model import CleanableBaseModel


class BillCreateSchema(CleanableBaseModel):
    bank_account_id: UUID = Field(..., alias="bank_account")
    number: str = Field(..., max_length=255, alias="bill_number")
    date: int = Field(..., ge=0, alias="bill_date")
    contract_id: Optional[UUID] = Field(None, alias="contract")
    buyer_id: Optional[UUID] = Field(None, alias="buyer")
    seller_id: Optional[UUID] = Field(None, alias="seller")
    company_id: UUID = Field(..., alias="company")

    @model_validator(mode="after")
    def check_contract_or_parties(self) -> "BillCreateSchema":
        if not self.contract_id:
            if not self.buyer_id or not self.seller_id:
                raise HTTPException(
                    status_code=400,
                    detail="""Either 'contract' must be provided, 
                    or both 'buyer' and 'seller' must be specified.""",
                )
        return self

    class Config:
        from_attributes = True
        populate_by_name = True


class BillResponseSchema(CleanableBaseModel):
    bill_id: UUID

    class Config:
        from_attributes = True


class BillEditSchema(CleanableBaseModel):
    bank_account_id: Optional[UUID] = Field(None, alias="bank_account")
    number: Optional[str] = Field(None, alias="bill_number")
    date: Optional[int] = Field(None, alias="bill_date")
    contract_id: Optional[UUID] = Field(None, alias="contract")
    buyer_id: Optional[UUID] = Field(None, alias="buyer")
    seller_id: Optional[UUID] = Field(None, alias="seller")
    company_id: Optional[UUID] = Field(None, alias="company")

    class Config:
        from_attributes = True
        populate_by_name = True


class BillSchema(CleanableBaseModel):
    bill_id: UUID
    bill_number: str
    bill_date: int
    bank_account: UUID
    contract: Optional[UUID] = None
    buyer: UUID
    seller: UUID
    company: UUID
    summ: Decimal

    class Config:
        from_attributes = True
        populate_by_name = True


class BillListResponseSchema(CleanableBaseModel):
    total: int
    bills: List[BillSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


def bill_filter_params(
    bank_account: Optional[UUID] = Query(
        None, description="Фильтр по банковскому счету"
    ),
    contract: Optional[UUID] = Query(None, description="Фильтр по контракту"),
    company: Optional[UUID] = Query(None, description="Фильтр по компании"),
    buyer: Optional[UUID] = Query(None, description="Фильтр по заказчику"),
    seller: Optional[UUID] = Query(None, description="Фильтр по исполнителю"),
    bill_date_from: Optional[int] = Query(
        None, description="Фильтр по дате от (timestamp)"
    ),
    bill_date_to: Optional[int] = Query(
        None, description="Фильтр по дате до (timestamp)"
    ),
    sort_by: Optional[str] = Query("number", description="Поле сортировки"),
    order: Optional[str] = Query("desc", description="Порядок сортировки: asc/desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "bank_account": bank_account,
        "contract": contract,
        "company": company,
        "bill_date_from": bill_date_from,
        "bill_date_to": bill_date_to,
        "buyer": buyer,
        "seller": seller,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
