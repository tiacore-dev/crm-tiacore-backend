from typing import Optional, List
from pydantic import UUID4, field_validator, Field
from fastapi import Query, HTTPException
from app.pydantic_models.clean_model import CleanableBaseModel


class LegalEntityCreateSchema(CleanableBaseModel):
    legal_entity_name: str = Field(..., min_length=3, max_length=255)
    inn: str = Field(..., min_length=10, max_length=12)
    kpp: Optional[str] = Field(None, min_length=9, max_length=9)
    vat_rate: int = Field(..., ge=0, le=100)
    address: str = Field(..., min_length=5, max_length=255)
    entity_type: str = Field(...,
                             description="ID типа юр. лица (внешний ключ)")
    signer: Optional[str] = Field(None, min_length=3, max_length=255)
    company: UUID4 = Field(...,
                           description="ID компании (внешний ключ), UUID4")
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
        json_schema_extra = {
            "example": {
                "legal_entity_name": "ООО Ромашка",
                "inn": "1234567890",
                "kpp": "123456789",
                "vat_rate": 20,
                "address": "г. Москва, ул. Пушкина, д. 1",
                "entity_type": "string-id-type",
                "signer": "Иванов И.И.",
                "company": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "description": "Юр. лицо для контрактов"
            }
        }


class LegalEntitySchema(CleanableBaseModel):
    legal_entity_id: UUID4
    legal_entity_name: str = Field(..., max_length=255)
    inn: str = Field(..., min_length=10, max_length=12)
    kpp: Optional[str] = Field(None, min_length=9, max_length=9)
    vat_rate: int
    address: str = Field(..., max_length=255)
    entity_type: str  # Теперь хранит ID, а не строку
    signer: Optional[str] = Field(None, max_length=255)
    company: UUID4
    description: Optional[str] = None

    class Config:
        from_attributes = True


class LegalEntityResponseSchema(CleanableBaseModel):
    legal_entity_id: UUID4

    class Config:
        from_attributes = True


class LegalEntityListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Количество записей по фильтру
    # ✅ Используем `list`, а не `List[LegalEntitySchema]`
    entities: List[LegalEntitySchema]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class LegalEntityEditSchema(CleanableBaseModel):
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
