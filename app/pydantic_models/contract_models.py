from typing import List, Optional
from uuid import UUID

from fastapi import File, Form, Query, UploadFile
from pydantic import Field
from tiacore_lib.pydantic_models.clean_model import CleanableBaseModel
from tiacore_lib.utils.validate_helpers import normalize_form_field


class ContractCreateSchema(CleanableBaseModel):
    name: str = Field(..., alias="contract_name")
    date: int = Field(..., alias="contract_date")
    comment: Optional[str] = None
    file: Optional[UploadFile | str | None] = None
    status_id: str = Field(..., alias="status")
    buyer_id: Optional[UUID] = Field(None, alias="buyer")
    seller_id: Optional[UUID] = Field(None, alias="seller")
    company_id: UUID = Field(..., alias="company")

    @classmethod
    def as_form(
        cls,
        contract_name=Form(...),
        contract_date=Form(...),
        buyer=Form(...),
        seller=Form(...),
        comment=Form(None),
        file: UploadFile | str | None = File(None),
        status=Form(...),
        company=Form(...),
    ):
        if isinstance(file, str) and file.strip() == "":
            file = None

        return cls(
            contract_name=contract_name,
            contract_date=contract_date,
            buyer=buyer,
            seller=seller,
            comment=comment,
            file=file,
            status=status,
            company=company,
        )

    class Config:
        from_attributes = True
        populate_by_name = True


class ContractSchema(CleanableBaseModel):
    contract_id: UUID
    contract_name: str
    contract_date: int
    buyer: UUID
    seller: UUID
    s3_key: Optional[str] = None
    status: str
    comment: Optional[str] = None
    company: UUID

    class Config:
        from_attributes = True
        populate_by_name = True


class ContractListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Количество записей по фильтру
    # ✅ Используем `list`, а не `List[ContractSchema]`
    contracts: List[ContractSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class ContractResponseSchema(CleanableBaseModel):
    contract_id: UUID

    class Config:
        from_attributes = True
        populate_by_name = True


class ContractEditSchema(CleanableBaseModel):
    name: Optional[str] = Field(None, alias="contract_name")
    date: Optional[int] = Field(None, alias="contract_date")
    comment: Optional[str] = None
    file: Optional[UploadFile | str] = None
    status_id: Optional[str] = Field(None, alias="status")
    buyer_id: Optional[UUID] = Field(None, alias="buyer")
    seller_id: Optional[UUID] = Field(None, alias="seller")
    company_id: Optional[UUID] = Field(None, alias="company")

    @classmethod
    def as_form(
        cls,
        contract_name: Optional[str] = Form(None),
        contract_date: Optional[int] = Form(None),
        buyer: Optional[str] = Form(None),
        seller: Optional[str] = Form(None),
        comment: Optional[str] = Form(None),
        file: Optional[str | UploadFile] = File(None),
        status: Optional[str] = Form(None),
        company: Optional[UUID] = Form(None),
    ):
        return cls(
            contract_name=normalize_form_field(contract_name, str),  # type: ignore[arg-type]
            contract_date=normalize_form_field(contract_date, int),  # type: ignore[arg-type]
            buyer=normalize_form_field(buyer, UUID),  # type: ignore[arg-type]
            seller=normalize_form_field(seller, UUID),  # type: ignore[arg-type]
            comment=normalize_form_field(comment, str),  # type: ignore[arg-type]
            file=None if isinstance(file, str) and file.strip() == "" else file,
            status=normalize_form_field(status, str),  # type: ignore[arg-type]
            company=normalize_form_field(company, UUID),  # type: ignore[arg-type]
        )

    class Config:
        from_attributes = True
        populate_by_name = True


def contract_filter_params(
    buyer: Optional[UUID] = Query(None, description="Фильтр по покупателю"),
    seller: Optional[UUID] = Query(None, description="Фильтр по продавцу"),
    company: Optional[UUID] = Query(None, description="Фильтр по компании"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    contract_date_to: Optional[int] = Query(None, description="Фильтр по дате от"),
    contract_date_from: Optional[int] = Query(None, description="Фильтр по дате до"),
    sort_by: Optional[str] = Query("contract_name", description="Поле сортировки"),
    order: Optional[str] = Query("asc", description="Порядок сортировки: asc/desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "buyer": buyer,
        "seller": seller,
        "company": company,
        "status": status,
        "contract_date_from": contract_date_from,
        "contract_date_to": contract_date_to,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
