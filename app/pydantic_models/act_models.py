from typing import Optional
from pydantic import BaseModel, UUID4, field_validator, Field
from fastapi import Query, HTTPException


class ActCreateSchema(BaseModel):
    act_number: str = Field(..., min_length=3, max_length=255)
    act_date: int = Field(..., ge=0)  # Unix timestamp
    contract: UUID4 = Field(...)

    @field_validator(
        "act_number", "act_date", "contract"
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


class ActResponseSchema(BaseModel):
    act_id: UUID4

    class Config:
        from_attributes = True


class ActEditSchema(BaseModel):
    act_number: Optional[str] = None
    act_date: Optional[int] = None
    contract: Optional[UUID4] = None

    class Config:
        from_attributes = True


def act_filter_params(
    contract: Optional[UUID4] = Query(None, description="Фильтр по контракту"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "contract": contract,
        "page": page,
        "page_size": page_size,
    }
