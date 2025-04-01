from typing import Optional, List
from pydantic import BaseModel, UUID4
from fastapi import Query, Form


class GenerateFileSchema(BaseModel):
    template_id: UUID4 = Form(...)
    entity_id: UUID4 = Form(...)
    extention: str = Form(...)


class TemplateResponseSchema(BaseModel):
    template_id: UUID4

    class Config:
        from_attributes = True


class TemplateSchema(BaseModel):
    template_id: UUID4
    template_name: str
    description: str
    company: UUID4
    entity: str
    s3_key: str

    class Config:
        from_attributes = True


class TemplateListResponseSchema(BaseModel):
    total: int
    templates: List[TemplateSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


def template_filter_params(
    company: Optional[UUID4] = Query(
        None, description="Фильтр по компании"),
    search: Optional[str] = Query(None, description="Фильтр поиска"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "company": company,
        "search": search,
        "page": page,
        "page_size": page_size,
    }
