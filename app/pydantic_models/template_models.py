from typing import Optional, List, Union
from pydantic import UUID4
from fastapi import Query, Form, UploadFile, File
from app.utils.validate_helpers import normalize_form_field
from app.pydantic_models.clean_model import CleanableBaseModel


class GenerateFileSchema(CleanableBaseModel):
    template_id: UUID4 = Form(...)
    entity_id: UUID4 = Form(...)
    is_pdf: Optional[bool] = Form(False)


class TemplateResponseSchema(CleanableBaseModel):
    template_id: UUID4

    class Config:
        from_attributes = True


class TemplateSchema(CleanableBaseModel):
    template_id: UUID4
    template_name: str
    description: Optional[str] = None
    company: UUID4
    entity: str
    s3_key: str

    class Config:
        from_attributes = True


class TemplateListResponseSchema(CleanableBaseModel):
    total: int
    templates: List[TemplateSchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


def template_filter_params(
    company: Optional[UUID4] = Query(
        None, description="Фильтр по компании"),
    entity: Optional['str'] = Query(None, description="Фильтр по типу"),
    search: Optional[str] = Query(None, description="Фильтр поиска"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "company": company,
        "entity": entity,
        "search": search,
        "page": page,
        "page_size": page_size,
    }


class TemplateCreateSchema(CleanableBaseModel):
    template_name: str
    description: Optional[str]
    company: UUID4
    entity: str
    file: UploadFile

    @classmethod
    def as_form(
        cls,
        template_name: str = Form(...),
        description: Optional[str] = Form(None),
        company: UUID4 = Form(...),
        entity: str = Form(...),
        file: UploadFile = File(...),
    ):
        return cls(
            template_name=template_name,
            description=description,
            company=company,
            entity=entity,
            file=file
        )


class TemplateEditSchema(CleanableBaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    company: Optional[UUID4] = None
    entity: Optional[str] = None
    file: Optional[UploadFile] = None

    @classmethod
    def as_form(
        cls,
        template_name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        company: Optional[str] = Form(None),  # как строка из формы
        entity: Optional[str] = Form(None),
        file: Optional[Union[str, UploadFile]] = File(None),
    ):
        return cls(
            template_name=normalize_form_field(template_name, str),
            description=normalize_form_field(description, str),
            company=normalize_form_field(company, UUID4),
            entity=normalize_form_field(entity, str),
            file=None if isinstance(
                file, str) and file.strip() == "" else file,
        )
