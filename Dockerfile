# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только requirements.txt для использования кеша pip
COPY requirements.txt .

# Устанавливаем зависимости (этап, который хорошо кешируется)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код проекта
COPY . .

# Установка LibreOffice (если можно — лучше вынести это в отдельный слой до requirements)
RUN apt update && \
    apt install -y libreoffice libreoffice-writer libreoffice-calc && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Запуск
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]
