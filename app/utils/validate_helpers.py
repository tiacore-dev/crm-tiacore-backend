import re
from pydantic import UUID4


def sanitize_input(value: str) -> str:
    """Удаляет XSS-атаку, но сохраняет текст"""
    value = re.sub(r'<[^>]*>', '', value)  # Убираем HTML-теги
    value = value.replace("alert", "")     # Убираем JavaScript
    return value.strip()  # Убираем лишние пробелы


def normalize_form_field(value, target_type):
    if isinstance(value, str) and value.strip() == "":
        return None
    if target_type == int:
        return int(value) if value is not None else None
    if target_type == UUID4:
        return UUID4(value) if value is not None else None
    return value
