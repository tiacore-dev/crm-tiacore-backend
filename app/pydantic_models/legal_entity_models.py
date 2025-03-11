from typing import Optional
from pydantic import BaseModel, UUID4, field_validator, Field
from fastapi import Query, HTTPException


class LegalEntityCreateSchema(BaseModel):
    legal_entity_name: str = Field(..., min_length=3, max_length=255)
    inn: str = Field(..., min_length=10, max_length=12)
    kpp: Optional[str] = Field(None, min_length=9, max_length=9)
    vat_rate: int = Field(..., ge=0, le=100)
    address: str = Field(..., min_length=5, max_length=255)
    entity_type: str = Field(...)
    signer: Optional[str] = Field(None, min_length=3, max_length=255)
    company: UUID4 = Field(...)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator(
        "legal_entity_name", "inn", "vat_rate", "address", "entity_type", "company"
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


class LegalEntityResponseSchema(BaseModel):
    legal_entity_id: UUID4

    class Config:
        from_attributes = True


class LegalEntityEditSchema(BaseModel):
    legal_entity_name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    vat_rate: Optional[int] = None
    address: Optional[str] = None
    entity_type: Optional[str] = None
    signer: Optional[str] = None
    company: Optional[UUID4] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


def legal_entity_filter_params(
    company: Optional[UUID4] = Query(
        None, description="Фильтр по компании"),
    entity_type: Optional[str] = Query(
        None, description="Фильтр по типу юр. лица"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "company": company,
        "entity_type": entity_type,
        "page": page,
        "page_size": page_size,
    }
