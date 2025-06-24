import os

from dotenv import load_dotenv
from tiacore_lib.config import ConfigName

from app import create_app
from metrics.logger import setup_logger

load_dotenv()


# Порт и биндинг
PORT = 8000

CONFIG_NAME = ConfigName(os.getenv("CONFIG_NAME", "Development"))

setup_logger()


app = create_app(config_name=CONFIG_NAME)


# 📌 Запуск Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(PORT), reload=True)
