from typing import Optional, List
from pydantic import UUID4, field_validator
from fastapi import Query, HTTPException, UploadFile, File, Form
from app.utils.validate_helpers import normalize_form_field
from app.pydantic_models.clean_model import CleanableBaseModel


class ContractCreateSchema(CleanableBaseModel):
    contract_name: str
    contract_date: int
    buyer: UUID4
    seller: UUID4
    comment: Optional[str] = None
    file: Optional[UploadFile] = None
    status: str
    company: UUID4

    @field_validator(
        "contract_name", "contract_date", "buyer", "seller", "status"
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

    @classmethod
    def as_form(
        cls,
        contract_name=Form(...),
        contract_date=Form(...),
        buyer=Form(...),
        seller=Form(...),
        comment=Form(None),
        file=File(None),
        status=Form(...),
        company=Form(...)
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
            company=company
        )

    class Config:
        from_attributes = True


class ContractSchema(CleanableBaseModel):
    contract_id: UUID4
    contract_name: str
    contract_date: int
    buyer: UUID4
    seller: UUID4
    s3_key: Optional[str] = None
    status: str
    comment: Optional[str] = None
    company: UUID4

    class Config:
        from_attributes = True


class ContractListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Количество записей по фильтру
    # ✅ Используем `list`, а не `List[ContractSchema]`
    contracts: List[ContractSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class ContractResponseSchema(CleanableBaseModel):
    contract_id: UUID4

    class Config:
        from_attributes = True


class ContractEditSchema(CleanableBaseModel):
    contract_name: Optional[str] = None
    contract_date: Optional[int] = None
    buyer: Optional[UUID4] = None
    seller: Optional[UUID4] = None
    comment: Optional[str] = None
    file: Optional[UploadFile] = None
    status: Optional[str] = None
    company: Optional[UUID4] = None

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
        company: Optional[UUID4] = Form(None)
    ):
        return cls(
            contract_name=normalize_form_field(contract_name, str),
            contract_date=normalize_form_field(contract_date, int),
            buyer=normalize_form_field(buyer, UUID4),
            seller=normalize_form_field(seller, UUID4),
            comment=normalize_form_field(comment, str),
            file=None if isinstance(
                file, str) and file.strip() == "" else file,
            status=normalize_form_field(status, str),
            company=normalize_form_field(company, UUID4)
        )

    class Config:
        from_attributes = True


def contract_filter_params(
    buyer: Optional[UUID4] = Query(None, description="Фильтр по покупателю"),
    seller: Optional[UUID4] = Query(None, description="Фильтр по продавцу"),
    company: Optional[UUID4] = Query(None, description="Фильтр по компании"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    contract_date_to: Optional[int] = Query(
        None, description="Фильтр по дате от"),
    contract_date_from: Optional[int] = Query(
        None, description="Фильтр по дате до"),
    sort_by: Optional[str] = Query(
        "contract_name", description="Поле сортировки"),
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc"),
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
