# Используем официальный образ Python в качестве базового
FROM python:3.12-slim

# Обновляем пакеты и устанавливаем LibreOffice (и зависимости)
RUN apt update && \
    apt install -y libreoffice libreoffice-writer libreoffice-calc && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Указываем команду запуска
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]
