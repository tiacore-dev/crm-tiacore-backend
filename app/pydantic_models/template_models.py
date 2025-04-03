from typing import Optional, List
from pydantic import BaseModel, UUID4
from fastapi import Query, Form, UploadFile, File


class GenerateFileSchema(BaseModel):
    template_id: UUID4 = Form(...)
    entity_id: UUID4 = Form(...)
    is_pdf: Optional[bool] = Form(False)


class TemplateResponseSchema(BaseModel):
    template_id: UUID4

    class Config:
        from_attributes = True


class TemplateSchema(BaseModel):
    template_id: UUID4
    template_name: str
    description: Optional[str] = None
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


class CreateTemplateSchema(BaseModel):
    template_name: str
    description: Optional[str] = None
    company: UUID4
    entity: str
    file: UploadFile

    @classmethod
    def as_form(
        cls,
        template_name=Form(...),
        company=Form(...),
        description=Form(None),
        entity=Form(...),
        file=File(...)
    ):
        return cls(
            template_name=template_name,
            company=company,
            description=description,
            entity=entity,
            file=file
        )


class EditTemplateSchema(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    company: Optional[UUID4] = None
    entity: Optional[str] = None
    file: Optional[UploadFile] = None

    @classmethod
    def as_form(
        cls,
        template_name=Form(None),
        company=Form(None),
        description=Form(None),
        entity=Form(None),
        file=File(None)
    ):
        return cls(
            template_name=template_name,
            company=company,
            description=description,
            entity=entity,
            file=file
        )
