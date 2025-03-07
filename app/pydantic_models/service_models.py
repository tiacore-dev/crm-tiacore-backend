from typing import Optional
from pydantic import BaseModel
from fastapi import Query


class ServiceSchema(BaseModel):
    service_id: str
    service_name: str


class ServiceCreateSchema(BaseModel):
    service_name: str


class ServiceResponseSchema(BaseModel):
    service_id: str


class ServiceEditSchema(BaseModel):
    service_name: str


class ServiceFilterParams(BaseModel):
    search: Optional[str] = Query(None, description="Фильтр по названию")
    sort_by: Optional[str] = Query(
        "service_name", description="Сортировка (по умолчанию name)")
    order: Optional[str] = Query(
        "asc", description="Порядок сортировки: asc/desc")
    page: Optional[int] = Query(1, description="Номер страницы")
    page_size: Optional[int] = Query(10, description="Размер страницы")
