import os
from dotenv import load_dotenv
from multiprocessing import cpu_count

load_dotenv()
# Получаем порт из переменной окружения или 5015
PORT = os.getenv("PORT", "5020")

bind = f"0.0.0.0:{PORT}"  # Указываем динамический порт
worker_class = "uvicorn.workers.UvicornWorker"
workers = max(2, min(4, cpu_count() // 2))
threads = 4

timeout = 120
keepalive = 5

loglevel = "info"
accesslog = "-"
errorlog = "-"

preload_app = True
worker_connections = 1000
max_requests = 500
max_requests_jitter = 50
