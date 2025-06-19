import json
import os
from io import BytesIO
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger
from tiacore_lib.config import get_settings
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tortoise.expressions import Q

from app.database.models import Templates
from app.dependencies.permissions import with_permission_and_template_check
from app.handlers.template_handler import handle_acts, handle_bills
from app.pydantic_models.template_models import (
    GenerateFileSchema,
    TemplateCreateSchema,
    TemplateEditSchema,
    TemplateListResponseSchema,
    TemplateResponseSchema,
    TemplateSchema,
    template_filter_params,
)
from app.s3.s3_manager import AsyncS3Manager

MEDIA_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}

template_router = APIRouter()


@template_router.post(
    "/add",
    response_model=TemplateResponseSchema,
    summary="Добавить шаблон",
    status_code=status.HTTP_201_CREATED,
)
async def add_template(
    data: TemplateCreateSchema = Depends(TemplateCreateSchema.as_form),
    context: dict = Depends(require_permission_in_context("add_template")),
):
    if not context.get("is_superadmin") and str(data.company) != context["company_id"]:
        raise HTTPException(
            status_code=403, detail="Вы не имеете доступа к этой компании"
        )

    file_bytes = await data.file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Не удалось загрузить данные файла")

    logger.info(
        f"""Тип загружаемых данных: {type(file_bytes)}, 
        размер: {len(file_bytes)} байт"""
    )

    filename = data.file.filename or "Unknown"
    manager = AsyncS3Manager()
    company_id = str(data.company) if data.company else "general"
    s3_key = await manager.upload_bytes(
        file_bytes, company_id, filename, entity="template"
    )

    template = await Templates.create(
        name=data.template_name,
        company_id=data.company,
        description=data.description,
        entity=data.entity,
        s3_key=s3_key,
    )
    return TemplateResponseSchema(template_id=template.id)


@template_router.patch(
    "/{template_id}", response_model=TemplateResponseSchema, summary="Изменить шаблон"
)
async def update_template(
    template_id: UUID,
    data: TemplateEditSchema = Depends(TemplateEditSchema.as_form),
    _=with_permission_and_template_check("edit_template"),
):
    template = await Templates.filter(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    update_data = {}
    if template.company_id:
        company_id = template.company_id

        if data.company and data.company != template.company_id:
            update_data["company_id"] = data.company
            update_data.pop("company")
            company_id = data.company

    # Обновление файла
    if data.file and not isinstance(data.file, UploadFile):
        raise HTTPException(status_code=400, detail="Недопустимый тип файла")

    if data.file:
        manager = AsyncS3Manager()
        file_bytes = await data.file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Не удалось загрузить файл")

        filename = data.file.filename or "Unknown"
        company_id_str = str(company_id) if company_id else ""

        await manager.delete_file(template.s3_key)
        new_s3_key = await manager.upload_bytes(
            file_bytes, company_id_str, filename, entity="template"
        )
        update_data["s3_key"] = new_s3_key

    # Обновление прочих полей
    if data.template_name:
        update_data["name"] = data.template_name
        update_data.pop("template_name")
    if data.description:
        update_data["description"] = data.description
    if data.entity:
        update_data["entity"] = data.entity

    await template.update_from_dict(update_data)
    await template.save()

    return TemplateResponseSchema(template_id=template.id)


@template_router.delete(
    "/{template_id}", summary="Удалить шаблон", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_template(
    template_id: UUID, _=with_permission_and_template_check("delete_template")
):
    template = await Templates.filter(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    manager = AsyncS3Manager()
    await manager.delete_file(template.s3_key)

    await template.delete()


@template_router.get(
    "/all",
    response_model=TemplateListResponseSchema,
    summary="Получение списка шаблонов",
)
async def get_templates(
    filters: dict = Depends(template_filter_params),
    context=Depends(require_permission_in_context("get_all_templates")),
):
    try:
        query = Q()
        if context["is_superadmin"]:
            company_filter = filters.get("company")
            if company_filter:
                query &= Q(company_id=company_filter) | Q(company_id=None)
        else:
            query &= Q(company_id=context["company_id"]) | Q(company_id=None)
        if filters.get("entity"):
            query &= Q(entity=filters["entity"])

        # ✅ Общее число записей
        total_count = await Templates.filter(query).count()

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        templates = (
            await Templates.filter(query)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return TemplateListResponseSchema(
            total=total_count,
            templates=[
                TemplateSchema(
                    template_id=template.id,
                    template_name=template.name,
                    description=template.description or "",
                    company=template.company_id,
                    entity=template.entity,
                    s3_key=template.s3_key,
                )
                for template in templates
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@template_router.post("/generate")
async def genereate_file(
    data: GenerateFileSchema,
    _=Depends(require_permission_in_context("generate_template")),
    settings=Depends(get_settings),
):
    logger.info(
        f"""🔧 Генерация файла запрошена пользователем: 
          шаблон: {data.template_id}, PDF: {data.is_pdf}"""
    )

    template = await Templates.get_or_none(id=data.template_id)
    if not template:
        logger.warning(f"📂 Шаблон не найден: {data.template_id}")
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    extension = os.path.splitext(template.s3_key)[-1].lower().replace(".", "")

    try:
        if template.entity.lower() == "act":
            document_data, entity_number = await handle_acts(data.entity_id)
        elif template.entity.lower() == "bill":
            document_data, entity_number = await handle_bills(data.entity_id)
        else:
            logger.error(f"❌ Неверная сущность: {template.entity}")
            raise HTTPException(status_code=400, detail="Неверная сущность")
    except Exception as e:
        logger.exception(f"⚠️ Ошибка при обработке сущности: {e}")
        raise
    manager = AsyncS3Manager()
    s3_url = await manager.generate_presigned_url(template.s3_key)
    payload = {
        "url": s3_url,
        "document_data": document_data,
        "name": f"{template.entity}_{entity_number}",
        "is_pdf": data.is_pdf,
    }
    logger.debug(
        f"document_data: {json.dumps(document_data, ensure_ascii=False, indent=2)}"
    )

    template_service_url = settings.TEMPLATE_SERVICE_URL
    logger.debug(
        f"""📡 Отправка запроса в template-service: 
        {template_service_url}, payload: {payload}"""
    )
    if not template_service_url:
        raise HTTPException(
            status_code=400, detail="отсутствует ссылка на template service"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(template_service_url, json=payload)

            if response.status_code != 200:
                logger.error(
                    f"""🚨 Ошибка от template-service: 
                        {response.status_code}, текст: {response.text}"""
                )
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            content_type = response.headers.get(
                "content-type", "application/octet-stream"
            )
            disposition = response.headers.get(
                "content-disposition", f'attachment; filename="document.{extension}"'
            )

            logger.info("✅ Файл успешно сгенерирован и получен от template-service")
            return StreamingResponse(
                BytesIO(response.content),
                media_type=content_type,
                headers={"Content-Disposition": disposition},
            )
    except httpx.RequestError as e:
        logger.exception(f"❌ Ошибка обращения к template-service: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка обращения к template-service: {e}"
        ) from e


@template_router.get("/{template_id}/download", summary="Скачивание шаблона")
async def download_template(
    template_id: UUID,
    _=Depends(require_permission_in_context("download_template")),
):
    template = await Templates.filter(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Счет не найден")
    manager = AsyncS3Manager()
    url = await manager.generate_presigned_url(template.s3_key)
    return url


@template_router.get(
    "/{template_id}", response_model=TemplateSchema, summary="Просмотр одного счета"
)
async def get_template(
    template_id: UUID, _=Depends(require_permission_in_context("view_template"))
):
    template = await Templates.filter(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return TemplateSchema(
        template_id=template.id,
        template_name=template.name,
        description=template.description or "",
        company=template.company_id,
        entity=template.entity,
        s3_key=template.s3_key,
    )
