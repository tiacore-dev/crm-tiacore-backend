from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from pydantic import Field
from fastapi import Query
from app.pydantic_models.clean_model import CleanableBaseModel


class EntityCompanyRelationCreateSchema(CleanableBaseModel):
    legal_entity: UUID = Field(..., description="UUID организации")
    company: UUID = Field(..., description="UUID компании")
    relation_type: Literal["buyer",
                           "seller"] = Field(..., description="Buyer или Seller")
    description: Optional[str] = Field(None, description="Описание связи")

    class Config:
        from_attributes = True


class EntityCompanyRelationSchema(CleanableBaseModel):
    entity_company_relation_id: UUID
    legal_entity_id: UUID
    company_id: UUID
    relation_type: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EntityCompanyRelationListResponseSchema(CleanableBaseModel):
    total: int
    relations: List[EntityCompanyRelationSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class EntityCompanyRelationResponseSchema(CleanableBaseModel):
    entity_company_relation_id: UUID

    class Config:
        from_attributes = True


class EntityCompanyRelationEditSchema(CleanableBaseModel):
    legal_entity: Optional[UUID] = None
    company: Optional[UUID] = None
    relation_type: Optional[Literal["buyer",
                                    "seller"]] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


def entity_company_filter_params(
    legal_entity: Optional[UUID] = Query(
        None, description="Фильтр по пользователю"),
    company: Optional[UUID] = Query(None, description="Фильтр по компании"),
    relation_type: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(
        "created_at", description="Поле сортировки"),
    order: Optional[str] = Query(
        "desc", description="Порядок сортировки: asc/desc"),
    description: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "legal_entity": legal_entity,
        "company": company,
        "relation_type": relation_type,
        "description": description,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
