from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from loguru import logger
from tiacore_lib.handlers.dependency_handler import require_permission_in_context
from tiacore_lib.utils.validate_helpers import validate_exists
from tortoise.expressions import Q

from app.database.models import Contract, ContractStatus
from app.dependencies.permissions import with_permission_and_seller_contract_check
from app.pydantic_models.contract_models import (
    ContractCreateSchema,
    ContractEditSchema,
    ContractListResponseSchema,
    ContractResponseSchema,
    ContractSchema,
    contract_filter_params,
)
from app.s3.s3_manager import AsyncS3Manager
from app.utils.permissions_get import ensure_seller_belongs_to_company

contract_router = APIRouter()


@contract_router.post(
    "/add",
    response_model=ContractResponseSchema,
    summary="Добавить контракт",
    status_code=status.HTTP_201_CREATED,
)
async def add_contract(
    data: ContractCreateSchema = Depends(ContractCreateSchema.as_form),
    context=Depends(require_permission_in_context("add_contract")),
):
    logger.debug("Добавление контракта")

    await validate_exists(ContractStatus, data.status_id, "Статус Контракта")

    if not context.get("is_superadmin"):
        await ensure_seller_belongs_to_company(data.seller_id, context["company_id"])

    s3_key = None
    if data.file and not isinstance(data.file, UploadFile):
        raise HTTPException(status_code=400, detail="Недопустимый тип файла")
    if data.file:
        logger.debug(f"Обработка файла: {data.file.filename}")

        file_bytes = await data.file.read()
        if not file_bytes:
            logger.warning("Файл пустой или не прочитан.")
            raise HTTPException(
                status_code=400, detail="Не удалось загрузить данные файла"
            )

        logger.info(
            f"""Тип загружаемых данных: {type(file_bytes)}, 
            размер: {len(file_bytes)} байт"""
        )

        filename = data.file.filename or "Unknown"
        manager = AsyncS3Manager()
        s3_key = await manager.upload_bytes(
            file_bytes,
            f"{data.buyer_id}+{data.seller_id}",
            filename,
            entity="contract",
        )
        logger.info(f"Файл успешно загружен в S3, ключ: {s3_key}")

    contract = await Contract.create(**data.model_dump())

    logger.info(f"Контракт успешно создан: {contract.id}")
    return ContractResponseSchema(contract_id=contract.id)


@contract_router.patch(
    "/{contract_id}", response_model=ContractResponseSchema, summary="Изменить контракт"
)
async def update_contract(
    contract_id: UUID,
    data: ContractEditSchema = Depends(ContractEditSchema.as_form),
    _=with_permission_and_seller_contract_check("edit_contract"),
):
    contract = await Contract.filter(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    if data.status_id:
        await validate_exists(ContractStatus, data.status_id, "Статус контракта")

    if data.file and not isinstance(data.file, UploadFile):
        raise HTTPException(status_code=400, detail="Недопустимый тип файла")
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    if data.file:
        manager = AsyncS3Manager()
        file_bytes = await data.file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Не удалось загрузить файл")

        # Удаляем старый файл
        if contract.s3_key:
            await manager.delete_file(contract.s3_key)
        filename = data.file.filename or "Unknown"
        # Загружаем новый
        new_s3_key = await manager.upload_bytes(
            file_bytes,
            f"{data.buyer_id}+{data.seller_id}",
            filename,
            entity="contract",
        )
        update_data["s3_key"] = new_s3_key
        update_data.pop("file")

    await contract.update_from_dict(update_data)
    await contract.save()

    return ContractResponseSchema(contract_id=contract.id)


@contract_router.delete(
    "/{contract_id}", summary="Удалить контракт", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contract(
    contract_id: UUID,
    _=with_permission_and_seller_contract_check("delete_contract"),
):
    contract = await Contract.filter(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    await contract.delete()


@contract_router.get(
    "/all",
    response_model=ContractListResponseSchema,
    summary="Получение списка контрактов",
)
async def get_contracts(
    filters: dict = Depends(contract_filter_params),
    context=Depends(require_permission_in_context("get_all_contracts")),
):
    try:
        query = Q()
        if context["is_superadmin"]:
            company_filter = filters.get("company")
            if company_filter:
                query &= Q(company_id=company_filter)
        else:
            query &= Q(company_id=context["company_id"])

        if filters.get("buyer"):
            query &= Q(buyer_id=filters["buyer"])
        if filters.get("seller"):
            query &= Q(seller_id=filters["seller"])
        if filters.get("status"):
            query &= Q(status_id=filters["status"])

        if filters.get("contract_name"):
            query &= Q(name__icontains=filters["contract_name"])

        if filters.get("contract_date_from"):
            try:
                date_from = int(filters["contract_date_from"])
                query &= Q(date__gte=date_from)
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail="contract_date_from должен быть целым числом (timestamp)",
                ) from e

        if filters.get("contract_date_to"):
            try:
                date_to = int(filters["contract_date_to"])
                query &= Q(date__lte=date_to)
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail="contract_date_to должен быть целым числом (timestamp)",
                ) from e

        sort_field_map = {
            "contract_number": "number",
            "contract_date": "date",
        }

        sort_by = filters.get("sort_by", "contract_number")
        sort_field = sort_field_map.get(sort_by)

        order = filters["order"]

        if sort_field not in {"name", "date"}:
            raise HTTPException(
                status_code=400, detail=f"Неверное поле сортировки: {sort_field}"
            )

        if order not in {"asc", "desc"}:
            raise HTTPException(
                status_code=400,
                detail="Порядок сортировки должен быть 'asc' или 'desc'",
            )

        # Префикс для порядка сортировки
        order_prefix = "" if order == "asc" else "-"
        total_count = await Contract.filter(query).count()
        contracts = (
            await Contract.filter(query)
            .prefetch_related("status")
            .order_by(f"{order_prefix}{sort_field}")
            .offset((filters["page"] - 1) * filters["page_size"])
            .limit(filters["page_size"])
        )

        return ContractListResponseSchema(
            total=total_count,
            contracts=[
                ContractSchema(
                    contract_id=contract.id,
                    contract_name=contract.name,
                    contract_date=contract.date,
                    buyer=contract.buyer_id,
                    seller=contract.seller_id,
                    status=contract.status.id,
                    s3_key=contract.s3_key,
                    comment=contract.comment,
                    company=contract.company_id,
                )
                for contract in contracts
            ],
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(status_code=400, detail="Некорректные данные") from e


@contract_router.get("/{contract_id}/download", summary="Скачивание файла контракта")
async def download_contract(
    contract_id: UUID,
    _=with_permission_and_seller_contract_check("download_contract"),
):
    contract = await Contract.filter(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")
    manager = AsyncS3Manager()
    url = await manager.generate_presigned_url(contract.s3_key)
    return url


@contract_router.get(
    "/{contract_id}", response_model=ContractSchema, summary="Просмотр одного контракта"
)
async def get_contract(
    contract_id: UUID,
    _=with_permission_and_seller_contract_check("view_contract"),
):
    contract = await Contract.filter(id=contract_id).prefetch_related("status").first()

    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    return ContractSchema(
        contract_id=contract.id,
        contract_name=contract.name,
        contract_date=contract.date,
        buyer=contract.buyer_id,
        seller=contract.seller_id,
        status=contract.status.id,
        s3_key=contract.s3_key,
        comment=contract.comment,
        company=contract.company_id,
    )
