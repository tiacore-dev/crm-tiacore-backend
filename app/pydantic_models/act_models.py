from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, Query
from pydantic import Field, model_validator
from tiacore_lib.pydantic_models.clean_model import CleanableBaseModel


class ActCreateSchema(CleanableBaseModel):
    number: str = Field(..., max_length=255, alias="act_number")
    date: int = Field(..., ge=0, alias="act_date")  # Unix timestamp
    contract_id: Optional[UUID] = Field(None, alias="contract")
    buyer_id: Optional[UUID] = Field(None, alias="buyer")
    seller_id: Optional[UUID] = Field(None, alias="seller")
    company_id: UUID = Field(..., alias="company")

    @model_validator(mode="after")
    def check_contract_or_parties(self) -> "ActCreateSchema":
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


class ActSchema(CleanableBaseModel):
    act_id: UUID
    act_number: str
    act_date: int
    contract: Optional[UUID] = None
    buyer: UUID
    seller: UUID
    company: UUID
    summ: Decimal

    class Config:
        from_attributes = True
        populate_by_name = True


class ActResponseSchema(CleanableBaseModel):
    act_id: UUID

    class Config:
        from_attributes = True


class ActListResponseSchema(CleanableBaseModel):
    total: int
    acts: List[ActSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ActEditSchema(CleanableBaseModel):
    number: Optional[str] = Field(None, alias="act_number")
    date: Optional[int] = Field(None, alias="act_date")
    contract_id: Optional[UUID] = Field(None, alias="contract")
    buyer_id: Optional[UUID] = Field(None, alias="buyer")
    seller_id: Optional[UUID] = Field(None, alias="seller")
    company_id: Optional[UUID] = Field(None, alias="company")

    class Config:
        from_attributes = True
        populate_by_name = True


def act_filter_params(
    contract: Optional[UUID] = Query(None, description="Фильтр по контракту"),
    company: Optional[UUID] = Query(None, description="Фильтр по компании"),
    buyer: Optional[UUID] = Query(None, description="Фильтр по заказчику"),
    seller: Optional[UUID] = Query(None, description="Фильтр по исполнителю"),
    act_date_to: Optional[int] = Query(None, description="Фильтр по дате до"),
    act_date_from: Optional[int] = Query(None, description="Фильтр по дате от"),
    sort_by: Optional[str] = Query("act_number", description="Поле сортировки"),
    order: Optional[str] = Query("desc", description="Порядок сортировки: asc/desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "contract": contract,
        "company": company,
        "act_date_from": act_date_from,
        "act_date_to": act_date_to,
        "buyer": buyer,
        "seller": seller,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
