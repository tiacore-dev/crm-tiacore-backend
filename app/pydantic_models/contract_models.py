from typing import Optional, List
from pydantic import BaseModel, UUID4, field_validator, Field
from fastapi import Query, HTTPException


class ContractCreateSchema(BaseModel):
    contract_name: str = Field(..., min_length=3, max_length=255)
    contract_date: int = Field(..., ge=0)  # Unix timestamp
    buyer: UUID4 = Field(...)
    seller: UUID4 = Field(...)
    comment: Optional[str] = Field(None, max_length=500)
    file: Optional[str] = Field(None, max_length=2083)
    status: str = Field(...)

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

    class Config:
        from_attributes = True


class ContractSchema(BaseModel):
    contract_id: UUID4
    contract_name: str
    contract_date: int  # Unix timestamp
    buyer: UUID4
    seller: UUID4
    file: str
    status: str

    class Config:
        from_attributes = True


class ContractListResponseSchema(BaseModel):
    total: int  # 🔥 Количество записей по фильтру
    # ✅ Используем `list`, а не `List[ContractSchema]`
    contracts: List[ContractSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class ContractResponseSchema(BaseModel):
    contract_id: UUID4

    class Config:
        from_attributes = True


class ContractEditSchema(BaseModel):
    contract_name: Optional[str] = None
    contract_date: Optional[int] = None
    buyer: Optional[UUID4] = None
    seller: Optional[UUID4] = None
    comment: Optional[str] = None
    file: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


def contract_filter_params(
    buyer: Optional[UUID4] = Query(None, description="Фильтр по покупателю"),
    seller: Optional[UUID4] = Query(None, description="Фильтр по продавцу"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "buyer": buyer,
        "seller": seller,
        "status": status,
        "page": page,
        "page_size": page_size,
    }
