from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from tortoise.expressions import Q
from loguru import logger
from app.database.models import Templates, Company
from app.pydantic_models.template_models import (
    TemplateResponseSchema,
    template_filter_params,
    TemplateSchema,
    TemplateListResponseSchema
)
from app.handlers.auth import get_current_user
from app.s3.s3_manager import AsyncS3Manager

template_router = APIRouter()


@template_router.post(
    "/add",
    response_model=TemplateResponseSchema,
    summary="Добавить шаблон",
    status_code=status.HTTP_201_CREATED
)
async def add_template(template_name: str = Form(...),
                       company: UUID = Form(...),
                       description: Optional[str] = Form(None),
                       entity: str = Form(...),
                       file: UploadFile = File(...),
                       username: str = Depends(get_current_user)):
    try:
        company_obj = await Company.get_or_none(company_id=company)
        if not company_obj:
            raise HTTPException(
                status_code=400, detail="Компания не найдена"
            )

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=400, detail="Не удалось загрузить данные файла"
            )

        logger.info(
            f"Тип загружаемых данных: {type(file_bytes)}, размер: {len(file_bytes)} байт")

        filename = file.filename
        manager = AsyncS3Manager()
        s3_key = await manager.upload_bytes(file_bytes, company, filename)

        template = await Templates.create(
            template_name=template_name,
            company=company_obj,
            description=description,
            entity=entity,
            s3_key=s3_key)
        return {"template_id": str(template.template_id)}

    except Exception as e:
        logger.exception("Ошибка при создании счета")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@template_router.patch(
    "/{template_id}",
    response_model=TemplateResponseSchema,
    summary="Изменить шаблон"
)
async def update_template(
    template_id: UUID,
    template_name: Optional[str] = Form(None),
    company: Optional[UUID] = Form(None),
    description: Optional[str] = Form(None),
    entity: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    username: str = Depends(get_current_user)
):
    template = await Templates.filter(template_id=template_id).prefetch_related("company").first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    update_data = {}
    company_id = template.company.company_id

    # Обновление компании, если нужно
    if company and company != template.company.company_id:
        company_obj = await Company.get_or_none(company_id=company)
        if not company_obj:
            raise HTTPException(status_code=400, detail="Компания не найдена")
        update_data["company"] = company_obj
        company_id = company

    # Обновление файла
    if file:
        manager = AsyncS3Manager()
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=400, detail="Не удалось загрузить файл")

        # Удаляем старый файл
        await manager.delete_file(template.s3_key)

        # Загружаем новый
        new_s3_key = await manager.upload_bytes(file_bytes, company_id, file.filename)
        update_data["s3_key"] = new_s3_key

    # Обновление прочих полей
    if template_name:
        update_data["template_name"] = template_name
    if description:
        update_data["description"] = description
    if entity:
        update_data["entity"] = entity

    await template.update_from_dict(update_data)
    await template.save()

    return {"template_id": str(template.template_id)}


@template_router.delete(
    "/{template_id}",
    summary="Удалить шаблон",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_template(template_id: UUID, username: str = Depends(get_current_user)):
    template = await Templates.filter(template_id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    manager = AsyncS3Manager()
    await manager.delete_file(template.s3_key)

    await template.delete()
    # return {"message": "Счет удалён"}


@template_router.get(
    "/all",
    response_model=TemplateListResponseSchema,
    summary="Получение списка счетов"
)
async def get_templates(filters: dict = Depends(template_filter_params), username: str = Depends(get_current_user)):
    try:
        query = Q()
        if filters.get("company"):
            query &= Q(company_id=filters["company"])
        # if filters.get("search"):
        #     query &= Q(bank_account_id=filters["bank_account"])

        # ✅ Общее число записей
        total_count = await Templates.filter(query).count()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        templates = await Templates.filter(query) \
            .prefetch_related("company") \
            .offset((page - 1) * page_size) \
            .limit(page_size)

        return TemplateListResponseSchema(
            total=total_count,
            templates=[
                TemplateSchema(
                    template_id=template.template_id,
                    template_name=template.template_name,
                    description=template.description,
                    company=template.company.company_id,
                    entity=template.entity,
                    s3_key=template.s3_key
                )
                for template in templates
            ]
        )

    except Exception as e:
        logger.exception("Ошибка при получении списка счетов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@template_router.get(
    "/{template_id}/download",
    # response_model=TemplateSchema,
    summary="Скачивание шаблона"
)
async def download_template(template_id: UUID, username: str = Depends(get_current_user)):
    template = await Templates.filter(template_id=template_id).prefetch_related("company").first()
    if not template:
        raise HTTPException(status_code=404, detail="Счет не найден")
    manager = AsyncS3Manager()
    url = await manager.generate_presigned_url(template.s3_key)
    return url


@template_router.get(
    "/{template_id}",
    response_model=TemplateSchema,
    summary="Просмотр одного счета"
)
async def get_template(template_id: UUID, username: str = Depends(get_current_user)):
    template = await Templates.filter(template_id=template_id).prefetch_related("company").first()
    if not template:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return TemplateSchema(
        template_id=template.template_id,
        template_name=template.template_name,
        description=template.description,
        company=template.company.company_id,
        entity=template.entity,
        s3_key=template.s3_key
    )
