import sys
from loguru import logger


def setup_logger():

    # Конфигурация Loguru
    logger.remove()  # Удаляем стандартный обработчик
    logger.add(
        sys.stdout,  # Логи в консоль
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="DEBUG",
    )
    logger.add(
        "logs/app.log",  # Логи в файл
        rotation="10 MB",  # Ротация файла (каждые 10 MB)
        retention="7 days",  # Хранить логи 7 дней
        level="DEBUG",
        compression="zip",  # Сжимать старые логи
    )

# Если хотите, чтобы логгер вел себя как синглтон:
