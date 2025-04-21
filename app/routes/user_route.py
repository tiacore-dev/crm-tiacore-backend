from uuid import UUID
import bcrypt
from fastapi import APIRouter, Depends, Path, HTTPException, Body, status
from loguru import logger
from tortoise.expressions import Q
from app.handlers.depends import require_permission_in_context
from app.dependencies.permissions import with_permission_and_company_check
from app.database.models import User, create_user, UserCompanyRelation, UserRole, Company
from app.pydantic_models.user_models import (
    UserCreateSchema, UserEditSchema, user_filter_params, UserResponseSchema, UserListResponseSchema, UserSchema
)


user_router = APIRouter()


@user_router.post(
    "/add", response_model=UserResponseSchema,
    summary="Добавление нового пользователя",
    status_code=status.HTTP_201_CREATED)
async def add_user(data: UserCreateSchema = Body(...),
                   context=Depends(require_permission_in_context("add_user"))
                   ):
    # Логируем без пароля
    logger.info(f"Создание пользователя: {data.dict(exclude={'password'})}")
    try:
        existing_user = await User.get_or_none(username=data.username)
        if existing_user:
            logger.warning(
                f"Пользователь с логином {data.username} уже существует")
            raise HTTPException(
                status_code=400, detail="Имя пользователя занято")
        logger.debug(f"Попытка создать пользователя {data.username}")
        user = await create_user(
            username=data.username,
            full_name=data.full_name,
            position=data.position,
            password=data.password
        )
        logger.debug(f"Пользователь создан: {user.user_id}")
        if not user:
            logger.error("Не удалось создать пользователя")
            raise HTTPException(
                status_code=500, detail="Не удалось создать пользователя")
        logger.success(
            f"Пользователь {user.username} ({user.user_id}) успешно создан")
        role = await UserRole.get_or_none(role_system_name='user')
        company = await Company.get_or_none(company_id=context['company'])
        if role and company:
            await UserCompanyRelation.create(user=user, company=company, role=role)
        return {"user_id": str(user.user_id)}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Ошибка при создании пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.patch(
    "/{user_id}",
    response_model=UserResponseSchema,
    summary="Изменение пользователя"
)
async def edit_user(
    user_id: UUID,
    data: UserEditSchema = Body(...),
    context=with_permission_and_company_check("edit_user")
):
    """
    Обновление пользователя по ID, переданному в URL.
    """
    logger.info(
        f"Обновление пользователя {user_id}: {data.dict(exclude_unset=True)}")
    try:
        # Исключаем поля, которые не были переданы
        # Исключаем поля, которые не были переданы
        update_data = data.dict(exclude_unset=True)

        if 'password' in update_data:  # Если передан пароль, хешируем его
            update_data['password_hash'] = bcrypt.hashpw(
                update_data.pop('password').encode(), bcrypt.gensalt()).decode()
        updated_rows = None
        if update_data:  # Обновляем только если есть данные для обновления
            updated_rows = await User.filter(user_id=user_id).update(**update_data)

        if not updated_rows:
            logger.warning(f"Пользователь {user_id} не найден")
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        logger.success(f"Пользователь {user_id} успешно обновлён")
        return {"user_id": str(user_id)}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при обновлении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.delete(
    "/{user_id}",
    summary="Удаление пользователя",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
    user_id: UUID,
    context=with_permission_and_company_check("delete_user")
):
    logger.info(f"Удаление пользователя {user_id}")
    try:
        deleted_count = await User.filter(user_id=user_id).first()
        if deleted_count.username == "admin":
            raise HTTPException(
                status_code=403, detail="вы не можете удалить администратора.")
        await deleted_count.delete()
        if not deleted_count:
            logger.warning(f"Пользователь {user_id} не найден")
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        logger.success(f"Пользователь {user_id} успешно удален")
        # return {"detail": "Пользователь успешно удален"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception("Ошибка при удалении пользователя")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.get("/all", response_model=UserListResponseSchema, summary="Просмотр пользователей")
async def get_users(
    filters: dict = Depends(user_filter_params),
    context=Depends(require_permission_in_context("get_all_users"))
):
    try:
        query = Q()
        search_value = filters.get("search")
        if search_value:
            query &= Q(username__icontains=search_value)

        company_filter = filters.get("company")

        if context["is_superadmin"]:
            if company_filter:
                # 🔍 фильтрация по переданной компании
                related_user_ids = await UserCompanyRelation.filter(
                    company=company_filter
                ).values_list("user_id", flat=True)

                if related_user_ids:
                    query &= Q(user_id__in=related_user_ids)
                else:
                    return UserListResponseSchema(total=0, users=[])
            # 🆓 без company — видит всех
        else:
            # 🔒 обычный пользователь — только свою компанию
            related_user_ids = await UserCompanyRelation.filter(
                company=context["company"]
            ).values_list("user_id", flat=True)

            if related_user_ids:
                query &= Q(user_id__in=related_user_ids)
            else:
                return UserListResponseSchema(total=0, users=[])

        order_by = f"{'-' if filters.get('order') == 'desc' else ''}{filters.get('sort_by', 'username')}"
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 10)

        # ✅ Получаем общее количество записей
        total_count = await User.filter(query).count()

        # ✅ Достаём сразу в виде словарей (ускоряет работу)
        users = await User.filter(query).order_by(order_by).offset(
            (page - 1) * page_size
        ).limit(page_size).values("user_id", "username", "full_name", "position")

        return UserListResponseSchema(
            total=total_count,
            # ✅ Преобразуем словари в Pydantic
            users=[UserSchema(**user) for user in users]
        )
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при получении списка пользователей")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.get("/{user_id}", response_model=UserSchema, summary="Просмотр пользователя")
async def get_user(
    user_id: UUID = Path(..., title="ID пользователя",
                         description="ID просматриваемого пользователя"),
    context: dict = Depends(require_permission_in_context("view_user"))
):
    logger.info(f"Получен запрос на просмотр пользователя: {user_id}")
    try:
        user_data = await User.get_or_none(user_id=user_id).values()
        if user_data is None:
            logger.warning(f"Пользователь {user_id} не найден")
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        # 🔐 Проверка доступа
        if not context["is_superadmin"]:
            # Получаем список user_id в рамках текущей компании
            allowed_user_ids = await UserCompanyRelation.filter(
                company=context["company"]
            ).values_list("user_id", flat=True)

            if user_id not in allowed_user_ids:
                raise HTTPException(
                    status_code=403, detail="Нет доступа к этому пользователю")

        user_schema = UserSchema(**user_data)
        logger.success(f"Найден пользователь: {user_schema}")
        return user_schema

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.exception("Ошибка при просмотре пользователя")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
