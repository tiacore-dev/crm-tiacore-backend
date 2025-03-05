# Используем официальный образ Python в качестве базового
FROM python:3.12-slim

# Указываем рабочую директорию внутри контейнера
WORKDIR /app


# Копируем файл зависимостей в рабочую директорию
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt


# Копируем весь код приложения в рабочую директорию
COPY . .


CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8001"]
