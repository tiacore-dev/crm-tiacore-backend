import html
import re
import unicodedata
from typing import Any, Type, TypeVar, cast
from uuid import UUID

from pydantic import UUID4


def sanitize_input(value: str, max_length: int = 255) -> str:
    """Очистка строки от XSS, пробелов, html-сущностей, невидимых символов и подмен"""
    if not isinstance(value, str):
        return value

    # 1. HTML entities → символы
    value = html.unescape(value)

    # 2. Удаление HTML-тегов
    value = re.sub(r"<[^>]*>", "", value)

    # 3. Удаление очевидных XSS-паттернов
    value = re.sub(r"(?i)(javascript:|data:|vbscript:|on\w+=)", "", value)
    value = value.replace("alert", "")

    # 4. Unicode нормализация (на всякий случай)
    value = unicodedata.normalize("NFC", value)

    # 5. Удаление невидимых символов (например, управляющие)
    value = "".join(c for c in value if unicodedata.category(c) not in ["Cc", "Cf"])

    # 7. Обрезаем до max_length
    if len(value) > max_length:
        value = value[:max_length]

    return value


T = TypeVar("T")


def normalize_form_field(value: Any, target_type: Type[T]) -> T | None:
    if isinstance(value, str) and value.strip() == "":
        return None
    if value is None:
        return None

    try:
        if target_type is int:
            return cast(T, int(value))
        if target_type is str:
            return cast(T, str(value))
        if target_type == UUID4 or target_type is UUID:
            return cast(T, UUID(value))  # 💡 фикс

        return cast(T, value) if isinstance(value, target_type) else None
    except Exception:
        return None
