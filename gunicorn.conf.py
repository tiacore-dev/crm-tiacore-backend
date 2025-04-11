from multiprocessing import cpu_count

# Получаем порт из переменной окружения или 5015
PORT = 8000

bind = f"0.0.0.0:{PORT}"  # Указываем динамический порт
worker_class = "uvicorn.workers.UvicornWorker"
workers = max(2, min(4, cpu_count() // 2))
threads = 4

timeout = 120
keepalive = 5

loglevel = "debug"
accesslog = "-"
errorlog = "-"

preload_app = True
worker_connections = 1000
max_requests = 500
max_requests_jitter = 50

preload_app = True
