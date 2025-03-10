from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Path, HTTPException
from loguru import logger
from tortoise.expressions import Q
from tortoise.contrib.pydantic import pydantic_model_creator
from app.handlers.auth import get_current_user
from app.database.models import User, create_user
from app.pydantic_models.user_models import (
    UserCreateSchema, UserEditSchema, user_filter_params, UserResponseSchema
)

UserSchema = pydantic_model_creator(User, name="UserSchema")

user_router = APIRouter()


@user_router.post("/add", response_model=UserResponseSchema, summary="Добавление нового пользователя")
async def add_user(data: UserCreateSchema, username: str = Depends(get_current_user)):
    try:
        user = await create_user(username=data.username, full_name=data.full_name, position=data.position, password=data.password)
        if not user:
            raise HTTPException(
                status_code=500, detail="Не удалось создать пользователя")
        return {"user_id": str(user.user_id)}
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.patch("/{user_id}/edit", response_model=UserResponseSchema, summary="Изменение пользователя")
async def edit_user(
        user_id: str = Path(..., title="ID пользователя",
                            description="ID изменяемого пользователя"),
        data: UserEditSchema = Depends(),  # Передача данных через тело запроса
        username: str = Depends(get_current_user)):
    """
    Обновление пользователя по ID, переданному в URL.
    """
    try:
        updated_rows = await User.filter(user_id=user_id).update(**data.dict(exclude_unset=True))

        if not updated_rows:
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        return {"user_id": user_id}
    except Exception as e:
        logger.error(f"Ошибка при обновлении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.delete("/{user_id}/delete", summary="Удаление пользователя")
async def delete_user(
        user_id: str = Path(..., title="ID пользователя",
                            description="ID удаляемого пользователя"),
        username: str = Depends(get_current_user)):
    try:
        deleted_count = await User.filter(user_id=user_id).delete()
        if not deleted_count:
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")
        return {"detail": "Пользователь успешно удален"}
    except Exception as e:
        logger.error(f"Ошибка при удалении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.get("/{user_id}/view", response_model=UserSchema, summary="Просмотр пользователя")
async def get_user(
    user_id: str = Path(..., title="ID пользователя",
                        description="ID просматриваемого пользователя"),
    username: str = Depends(get_current_user)
):
    try:
        logger.info(f"Получен запрос на просмотр пользователя: {user_id}")

        # Проверяем, корректен ли UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError as exc:
            logger.error(f"Некорректный UUID: {user_id}")
            raise HTTPException(
                status_code=400, detail="Некорректный формат ID пользователя") from exc

        # Получаем объект пользователя
        user = await User.get_or_none(user_id=user_uuid)
        if user is None:
            logger.warning(f"Пользователь {user_uuid} не найден")
            raise HTTPException(
                status_code=404, detail="Пользователь не найден")

        logger.info(f"Найден пользователь: {user}")

        # Используем правильную конвертацию
        user_schema = await UserSchema.from_tortoise_orm(user)
        logger.info(f"Успешно конвертировано: {user_schema}")
        return user_schema

    except Exception as e:
        logger.exception(f"Ошибка при просмотре пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e


@user_router.get("/all", response_model=List[UserSchema], summary="Получение списка пользователей с фильтрацией")
async def get_users(
    filters: dict = Depends(user_filter_params),
    username: str = Depends(get_current_user)
):
    try:
        logger.info(f"Получен запрос на список пользователей: {filters}")

        # Формируем динамический фильтр
        query = Q()
        if filters.get("search"):
            query &= Q(username__icontains=filters["search"])

        # Определяем порядок сортировки
        order_by = f"{'-' if filters['order'] == 'desc' else ''}{filters['sort_by']}"

        # Запрашиваем данные с фильтрацией, сортировкой и пагинацией
        users = await User.filter(query).order_by(order_by).offset((filters["page"] - 1) * filters["page_size"]).limit(filters["page_size"])

        # Конвертируем в Pydantic
        user_list = [await UserSchema.from_tortoise_orm(user) for user in users]

        logger.info(
            f"Найдено {len(user_list)} пользователей (страница {filters['page']})")
        return user_list

    except Exception as e:
        logger.exception(f"Ошибка при получении списка пользователей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера") from e
