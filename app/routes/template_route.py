from uuid import UUID
from io import BytesIO
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from tortoise.expressions import Q
from loguru import logger
from app.database.models import Templates, Company
from app.pydantic_models.template_models import (
    TemplateCreateSchema,
    TemplateEditSchema,
    TemplateResponseSchema,
    template_filter_params,
    TemplateSchema,
    TemplateListResponseSchema,
    GenerateFileSchema
)
from app.handlers.auth import get_current_user
from app.handlers.template_handler import handle_acts, handle_bills
from app.config import Settings
from app.s3.s3_manager import AsyncS3Manager

settings = Settings()

template_router = APIRouter()


@template_router.post(
    "/add",
    response_model=TemplateResponseSchema,
    summary="Добавить шаблон",
    status_code=status.HTTP_201_CREATED
)
async def add_template(data: TemplateCreateSchema = Depends(TemplateCreateSchema.as_form),
                       username: str = Depends(get_current_user)):
    try:
        company_obj = await Company.get_or_none(company_id=data.company)
        if not company_obj:
            raise HTTPException(
                status_code=400, detail="Компания не найдена"
            )

        file_bytes = await data.file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=400, detail="Не удалось загрузить данные файла"
            )

        logger.info(
            f"Тип загружаемых данных: {type(file_bytes)}, размер: {len(file_bytes)} байт")

        filename = data.file.filename
        manager = AsyncS3Manager()
        s3_key = await manager.upload_bytes(file_bytes, data.company, filename, entity="template")

        template = await Templates.create(
            template_name=data.template_name,
            company=company_obj,
            description=data.description,
            entity=data.entity,
            s3_key=s3_key)
        return {"template_id": str(template.template_id)}
    except HTTPException as http_exc:
        raise http_exc
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
    data: TemplateEditSchema = Depends(TemplateEditSchema.as_form),
    username: str = Depends(get_current_user)
):
    template = await Templates.filter(template_id=template_id).prefetch_related("company").first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    update_data = {}
    company_id = template.company.company_id

    # Обновление компании, если нужно
    if data.company and data.company != template.company.company_id:
        company_obj = await Company.get_or_none(company_id=data.company)
        if not company_obj:
            raise HTTPException(status_code=400, detail="Компания не найдена")
        update_data["company"] = company_obj
        company_id = data.company

    # Обновление файла
    if data.file:
        manager = AsyncS3Manager()
        file_bytes = await data.file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=400, detail="Не удалось загрузить файл")

        # Удаляем старый файл
        await manager.delete_file(template.s3_key)

        # Загружаем новый
        new_s3_key = await manager.upload_bytes(file_bytes, company_id, data.file.filename, entity="template")
        update_data["s3_key"] = new_s3_key

    # Обновление прочих полей
    if data.template_name:
        update_data["template_name"] = data.template_name
    if data.description:
        update_data["description"] = data.description
    if data.entity:
        update_data["entity"] = data.entity

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
                    description=template.description or "",
                    company=template.company.company_id,
                    entity=template.entity,
                    s3_key=template.s3_key
                )
                for template in templates
            ]
        )

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при получении списка счетов")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@template_router.get(
    "/{template_id}/download",
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
        description=template.description or "",
        company=template.company.company_id,
        entity=template.entity,
        s3_key=template.s3_key
    )

MEDIA_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf"
}


@template_router.post("/generate")
async def genereate_file(data: GenerateFileSchema, username: str = Depends(get_current_user)):
    logger.info(
        f"🔧 Генерация файла запрошена пользователем: {username}, шаблон: {data.template_id}, PDF: {data.is_pdf}")

    template = await Templates.get_or_none(template_id=data.template_id)
    if not template:
        logger.warning(f"📂 Шаблон не найден: {data.template_id}")
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    extension = os.path.splitext(template.s3_key)[-1].lower().replace('.', '')

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

    payload = {
        "s3_key": template.s3_key,
        "document_data": document_data,
        "name": f"{template.entity}_{entity_number}",
        "is_pdf": data.is_pdf
    }

    template_service_url = settings.TEMPLATE_SERVICE_URL
    logger.debug(
        f"📡 Отправка запроса в template-service: {template_service_url}, payload: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(template_service_url, json=payload)

            if response.status_code != 200:
                logger.error(
                    f"🚨 Ошибка от template-service: {response.status_code}, текст: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )

            content_type = response.headers.get(
                "content-type", "application/octet-stream")
            disposition = response.headers.get(
                "content-disposition", f'attachment; filename="document.{extension}"'
            )

            logger.info(
                "✅ Файл успешно сгенерирован и получен от template-service")
            return StreamingResponse(
                BytesIO(response.content),
                media_type=content_type,
                headers={"Content-Disposition": disposition}
            )
    except httpx.RequestError as e:
        logger.exception(f"❌ Ошибка обращения к template-service: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка обращения к template-service: {e}"
        ) from e
