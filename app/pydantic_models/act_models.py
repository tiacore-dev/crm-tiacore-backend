from typing import Optional, List
from pydantic import UUID4, field_validator, Field, model_validator
from fastapi import Query, HTTPException
from app.pydantic_models.clean_model import CleanableBaseModel


class ActCreateSchema(CleanableBaseModel):
    act_number: str = Field(..., min_length=3, max_length=255)
    act_date: int = Field(..., ge=0)  # Unix timestamp
    contract: Optional[UUID4] = Field(None)
    buyer: Optional[UUID4] = Field(None)
    seller: Optional[UUID4] = Field(None)

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

    @model_validator(mode="after")
    def check_contract_or_parties(self) -> 'ActCreateSchema':
        if not self.contract:
            if not self.buyer or not self.seller:
                raise HTTPException(
                    status_code=400,
                    detail="Either 'contract' must be provided, or both 'buyer' and 'seller' must be specified."
                )
        return self

    class Config:
        from_attributes = True


class ActSchema(CleanableBaseModel):
    act_id: UUID4
    act_number: str
    act_date: int
    contract: Optional[UUID4] = None
    buyer: UUID4
    seller: UUID4

    class Config:
        from_attributes = True


class ActResponseSchema(CleanableBaseModel):
    act_id: UUID4

    class Config:
        from_attributes = True


class ActListResponseSchema(CleanableBaseModel):
    total: int  # 🔥 Общее количество актов по фильтру
    acts: List[ActSchema]  # ✅ Используем `list`, а не `List[ActSchema]`

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Разрешаем нестандартные типы


class ActEditSchema(CleanableBaseModel):
    act_number: Optional[str] = None
    act_date: Optional[int] = None
    contract: Optional[UUID4] = None
    buyer: Optional[UUID4] = None
    seller: Optional[UUID4] = None

    class Config:
        from_attributes = True


def act_filter_params(
    contract: Optional[UUID4] = Query(None, description="Фильтр по контракту"),
    act_date_to: Optional[int] = Query(None, description="Фильтр по дате до"),
    act_date_from: Optional[int] = Query(
        None, description="Фильтр по дате от"),
    sort_by: Optional[str] = Query("act_date", description="Поле сортировки"),
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
):
    return {
        "contract": contract,
        "act_date_from": act_date_from,
        "act_date_to": act_date_to,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "page_size": page_size,
    }
