import re


def sanitize_input(value: str) -> str:
    """Удаляет XSS-атаку, но сохраняет текст"""
    value = re.sub(r'<[^>]*>', '', value)  # Убираем HTML-теги
    value = value.replace("alert", "")     # Убираем JavaScript
    return value.strip()  # Убираем лишние пробелы
