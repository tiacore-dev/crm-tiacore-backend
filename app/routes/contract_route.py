from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.expressions import Q
from loguru import logger
from app.database.models import Contract, ContractStatus, LegalEntity, EntityCompanyRelation
from app.pydantic_models.contract_models import (
    ContractCreateSchema,
    ContractResponseSchema,
    ContractEditSchema,
    contract_filter_params,
    ContractSchema,
    ContractListResponseSchema
)
from app.handlers.depends import require_permission_in_context
from app.dependencies.permissions import with_permission_and_seller_company_check
from app.utils.permissions_get import ensure_seller_belongs_to_company
from app.s3.s3_manager import AsyncS3Manager

contract_router = APIRouter()


@contract_router.post(
    "/add",
    response_model=ContractResponseSchema,
    summary="Добавить контракт",
    status_code=status.HTTP_201_CREATED
)
async def add_contract(
    data: ContractCreateSchema = Depends(ContractCreateSchema.as_form),
    context=Depends(require_permission_in_context("add_contract"))
):
    try:
        logger.debug(f"Полученные данные: {data.model_dump()}")

        buyer = await LegalEntity.get_or_none(legal_entity_id=data.buyer)
        seller = await LegalEntity.get_or_none(legal_entity_id=data.seller)
        status_obj = await ContractStatus.get_or_none(contract_status_id=data.status)

        if not buyer:
            logger.warning(f"Покупатель не найден: {data.buyer}")
        if not seller:
            logger.warning(f"Продавец не найден: {data.seller}")
        if not status_obj:
            logger.warning(f"Статус не найден: {data.status}")

        if not buyer or not seller or not status_obj:
            raise HTTPException(
                status_code=400,
                detail="Покупатель, продавец или статус не найдены"
            )
        if not context.get("is_superadmin"):
            await ensure_seller_belongs_to_company(seller, context["company"])

        s3_key = None
        if data.file:
            logger.debug(f"Обработка файла: {data.file.filename}")

            file_bytes = await data.file.read()
            if not file_bytes:
                logger.warning("Файл пустой или не прочитан.")
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось загрузить данные файла"
                )

            logger.info(
                f"Тип загружаемых данных: {type(file_bytes)}, размер: {len(file_bytes)} байт"
            )

            filename = data.file.filename
            manager = AsyncS3Manager()
            s3_key = await manager.upload_bytes(
                file_bytes,
                f"{data.buyer}+{data.seller}",
                filename,
                entity="contract"
            )
            logger.info(
                f"Файл успешно загружен в S3, ключ: {s3_key}")

        contract = await Contract.create(
            contract_name=data.contract_name,
            contract_date=data.contract_date,
            buyer=buyer,
            seller=seller,
            comment=data.comment,
            s3_key=s3_key,
            status=status_obj,
        )

        logger.info(
            f"Контракт успешно создан: {contract.contract_id}")
        return {"contract_id": str(contract.contract_id)}

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@contract_router.patch(
    "/{contract_id}",
    response_model=ContractResponseSchema,
    summary="Изменить контракт"
)
async def update_contract(
        contract_id: UUID,
        data: ContractEditSchema = Depends(ContractEditSchema.as_form),
        check_contract_access=with_permission_and_seller_company_check(
            permission="edit_contract",
            model=Contract,
            model_name="contract"
        )):
    contract = await Contract.filter(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    update_data = {}

    if data.buyer:
        buyer = await LegalEntity.get_or_none(legal_entity_id=data.buyer)
        if not buyer:
            raise HTTPException(status_code=400, detail="Покупатель не найден")
        update_data["buyer"] = buyer

    if data.seller:
        seller = await LegalEntity.get_or_none(legal_entity_id=data.seller)
        if not seller:
            raise HTTPException(status_code=400, detail="Продавец не найден")
        update_data["seller"] = seller

    if data.status:
        status_obj = await ContractStatus.get_or_none(contract_status_id=data.status)
        if not status_obj:
            raise HTTPException(status_code=400, detail="Статус не найден")
        update_data["status"] = status_obj

    if data.file:
        manager = AsyncS3Manager()
        file_bytes = await data.file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=400, detail="Не удалось загрузить файл")

        # Удаляем старый файл
        await manager.delete_file(contract.s3_key)

        # Загружаем новый
        new_s3_key = await manager.upload_bytes(file_bytes, f"{data.buyer}+{data.seller}", data.file.filename, entity="contract")
        update_data["s3_key"] = new_s3_key

    if data.contract_name:
        update_data['contract_name'] = data.contract_name
    if data.contract_date:
        update_data['contract_date'] = data.contract_date
    if data.comment:
        update_data['comment'] = data.comment

    await contract.update_from_dict(update_data)
    await contract.save()

    return {"contract_id": str(contract.contract_id)}


@contract_router.delete(
    "/{contract_id}",
    summary="Удалить контракт",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contract(
        contract_id: UUID,
        check_contract_access=with_permission_and_seller_company_check(
            permission="delete_contract",
            model=Contract,
            model_name="contract"
        )):
    contract = await Contract.filter(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    await contract.delete()


@contract_router.get(
    "/all",
    response_model=ContractListResponseSchema,
    summary="Получение списка контрактов"
)
async def get_contracts(filters: dict = Depends(contract_filter_params), context=Depends(require_permission_in_context("get_all_contracts"))):
    try:

        query = Q()
        if not context.get("is_superadmin"):
            seller_entity_ids = await EntityCompanyRelation.filter(
                company_id=context["company"],
                relation_type="seller"
            ).values_list("legal_entity_id", flat=True)
            query &= Q(seller_id__in=seller_entity_ids)

        if filters.get("buyer"):
            query &= Q(buyer_id=filters["buyer"])
        if filters.get("seller"):
            query &= Q(seller_id=filters["seller"])
        if filters.get("status"):
            query &= Q(status_id=filters["status"])

        if filters.get("contract_name"):
            query &= Q(contract_name__icontains=filters["contract_name"])

        if filters.get("contract_date_from"):
            try:
                date_from = int(filters["contract_date_from"])
                query &= Q(contract_date__gte=date_from)
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail="contract_date_from должен быть целым числом (timestamp)"
                ) from e

        if filters.get("contract_date_to"):
            try:
                date_to = int(filters["contract_date_to"])
                query &= Q(contract_date__lte=date_to)
            except ValueError as e:
                raise HTTPException(
                    status_code=422,
                    detail="contract_date_to должен быть целым числом (timestamp)"
                ) from e
        sort_field = filters["sort_by"]
        order = filters["order"]

        # Проверка и безопасное составление сортировочного поля
        # добавь другие поля, если нужно
        if sort_field not in {"contract_name", "contract_date"}:
            raise HTTPException(
                status_code=400,
                detail=f"Неверное поле сортировки: {sort_field}"
            )

        if order not in {"asc", "desc"}:
            raise HTTPException(
                status_code=400,
                detail="Порядок сортировки должен быть 'asc' или 'desc'"
            )

        # Префикс для порядка сортировки
        order_prefix = "" if order == "asc" else "-"
        total_count = await Contract.filter(query).count()
        contracts = await Contract.filter(query) \
            .prefetch_related("buyer", "seller", "status") \
            .order_by(f"{order_prefix}{sort_field}") \
            .offset((filters["page"] - 1) * filters["page_size"]) \
            .limit(filters["page_size"])

        return ContractListResponseSchema(
            total=total_count,
            contracts=[
                ContractSchema(
                    contract_id=contract.contract_id,
                    contract_name=contract.contract_name,
                    contract_date=contract.contract_date,
                    buyer=contract.buyer.legal_entity_id,  # Теперь ID
                    seller=contract.seller.legal_entity_id,  # Теперь ID
                    status=contract.status.contract_status_id,  # Теперь ID
                    s3_key=contract.s3_key,
                    comment=contract.comment
                )
                for contract in contracts
            ]
        )

    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка данных: {e}")
        raise HTTPException(
            status_code=400, detail="Некорректные данные") from e


@contract_router.get(
    "/{contract_id}/download",
    summary="Скачивание файла контракта"
)
async def download_contract(
        contract_id: UUID,
        check_contract_access=with_permission_and_seller_company_check(
            permission="download_contract",
            model=Contract,
            model_name="contract"
        )):
    contract = await Contract.filter(contract_id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")
    manager = AsyncS3Manager()
    url = await manager.generate_presigned_url(contract.s3_key)
    return url


@contract_router.get(
    "/{contract_id}",
    response_model=ContractSchema,
    summary="Просмотр одного контракта"
)
async def get_contract(
        contract_id: UUID,
        check_contract_access=with_permission_and_seller_company_check(
            permission="view_contract",
            model=Contract,
            model_name="contract"
        )):
    contract = await Contract.filter(contract_id=contract_id).prefetch_related("buyer", "seller", "status").first()

    if not contract:
        raise HTTPException(status_code=404, detail="Контракт не найден")

    return ContractSchema(
        contract_id=contract.contract_id,
        contract_name=contract.contract_name,
        contract_date=contract.contract_date,
        buyer=contract.buyer.legal_entity_id,
        seller=contract.seller.legal_entity_id,
        status=contract.status.contract_status_id,
        s3_key=contract.s3_key,
        comment=contract.comment
    )
