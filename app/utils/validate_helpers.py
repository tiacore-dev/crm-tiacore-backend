import re
import html
import unicodedata
from pydantic import UUID4


def sanitize_input(value: str, max_length: int = 255, html_safe: bool = True) -> str:
    """Очистка строки от XSS, пробелов, html-сущностей, невидимых символов и подмен"""
    if not isinstance(value, str):
        return value

    # 1. HTML entities → символы
    value = html.unescape(value)

    # 2. Удаление HTML-тегов
    value = re.sub(r'<[^>]*>', '', value)

    # 3. Удаление очевидных XSS-паттернов
    value = re.sub(r'(?i)(javascript:|data:|vbscript:|on\w+=)', '', value)
    value = value.replace("alert", "")

    # 4. Unicode нормализация (на всякий случай)
    value = unicodedata.normalize("NFC", value)

    # 5. Удаление невидимых символов (например, управляющие)
    value = ''.join(c for c in value if unicodedata.category(c)
                    not in ['Cc', 'Cf'])

    # 7. Обрезаем до max_length
    if len(value) > max_length:
        value = value[:max_length]

    return value


def normalize_form_field(value, target_type):
    if isinstance(value, str) and value.strip() == "":
        return None
    if target_type == int:
        return int(value) if value is not None else None
    if target_type == UUID4:
        return UUID4(value) if value is not None else None
    return value
