from typing import Optional
from pydantic import BaseModel, UUID4
from fastapi import Query


class LegalEntityCreateSchema(BaseModel):
    legal_entity_name: str
    inn: str
    kpp: Optional[str] = None
    vat_rate: int
    address: str
    entity_type: str
    signer: Optional[str] = None
    company: UUID4
    description: Optional[str] = None

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
