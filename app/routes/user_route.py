from uuid import UUID
import bcrypt
from fastapi import APIRouter, Depends, Path, HTTPException, Body, status
from loguru import logger
from tortoise.expressions import Q
from app.handlers.auth import get_current_user
from app.database.models import User, create_user
from app.pydantic_models.user_models import (
    UserCreateSchema, UserEditSchema, user_filter_params, UserResponseSchema, UserListResponseSchema, UserSchema
)


user_router = APIRouter()


@user_router.post("/add", response_model=UserResponseSchema, summary="Добавление нового пользователя", status_code=status.HTTP_201_CREATED)
async def add_user(data: UserCreateSchema = Body(...), username: str = Depends(get_current_user)):
    # Логируем без пароля
    logger.info(f"Создание пользователя: {data.dict(exclude={'password'})}")
    try:
        user = await create_user(
            username=data.username,
            full_name=data.full_name,
            position=data.position,
            password=data.password
        )
        if not user:
            logger.error("Не удалось создать пользователя")
            raise HTTPException(
                status_code=500, detail="Не удалось создать пользователя")

        logger.success(
            f"Пользователь {user.username} ({user.user_id}) успешно создан")
        return {"user_id": str(user.user_id)}
    except Exception as e:
        logger.exception("Ошибка при создании пользователя")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.patch("/{user_id}", response_model=UserResponseSchema, summary="Изменение пользователя")
async def edit_user(
        user_id: UUID = Path(..., title="ID пользователя",
                             description="ID изменяемого пользователя"),
        data: UserEditSchema = Body(...),
        username: str = Depends(get_current_user)):
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

        if update_data:  # Обновляем только если есть данные для обновления
            updated_rows = await User.filter(user_id=user_id).update(**update_data)

        if not updated_rows:
            logger.warning(f"Пользователь {user_id} не найден")
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        logger.success(f"Пользователь {user_id} успешно обновлён")
        return {"user_id": str(user_id)}
    except Exception as e:
        logger.exception("Ошибка при обновлении пользователя")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.delete("/{user_id}", summary="Удаление пользователя", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user_id: UUID = Path(..., title="ID пользователя",
                             description="ID удаляемого пользователя"),
        username: str = Depends(get_current_user)):
    logger.info(f"Удаление пользователя {user_id}")
    try:
        deleted_count = await User.filter(user_id=user_id).delete()
        if not deleted_count:
            logger.warning(f"Пользователь {user_id} не найден")
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        logger.success(f"Пользователь {user_id} успешно удален")
        # return {"detail": "Пользователь успешно удален"}
    except Exception as e:
        logger.exception("Ошибка при удалении пользователя")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.get(
    "/all",
    response_model=UserListResponseSchema,
    summary="Получение списка пользователей"
)
async def get_users(filters: dict = Depends(user_filter_params)):
    try:
        query = Q()
        search_value = filters.get("search")
        if search_value:
            query &= Q(username__icontains=search_value)

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

    except Exception as e:
        logger.exception("Ошибка при получении списка пользователей")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.get("/{user_id}", response_model=UserSchema, summary="Просмотр пользователя")
async def get_user(
    user_id: UUID = Path(..., title="ID пользователя",
                         description="ID просматриваемого пользователя"),
    username: str = Depends(get_current_user)
):
    logger.info(f"Получен запрос на просмотр пользователя: {user_id}")
    try:
        user = await User.get_or_none(user_id=user_id).values()
        if user is None:
            logger.warning(f"Пользователь {user_id} не найден")
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        # ✅ Создаём Pydantic-модель вручную
        user_schema = UserSchema(
            **user
        )

        logger.success(f"Найден пользователь: {user_schema}")
        return user_schema

    except Exception as e:
        logger.exception("Ошибка при просмотре пользователя")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
