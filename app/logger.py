import sys
from loguru import logger
from prometheus_client import Counter

# 📊 Prometheus counters
error_counter = Counter("fastapi_errors_total",
                        "Total number of FastAPI errors")
error_counter_by_user = Counter(
    "fastapi_errors_total_by_user",
    "Total number of errors per user",
    ["user_id", "login", "role"]
)


# 📈 Prometheus hook — простой, без user_id
def prometheus_hook(message):
    record = message.record
    if record["level"].no >= 40:  # 40 = ERROR
        error_counter.inc()
        try:
            error_counter_by_user.labels(
                user_id="unknown",
                login="system",
                role="system"
            ).inc()
        except Exception as e:
            print(f"[PrometheusHook] Ошибка при инкременте метрик: {e}")


# 🛠 Logger setup — простой текст, как раньше
def setup_logger():
    logger.remove()

    logger.add(
        sys.stdout,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | "
               "<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        colorize=True,
    )

    logger.add(
        "logs/app.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        # compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {function}:{line} - {message}",
        enqueue=True,
    )

    logger.add(prometheus_hook, level="ERROR")
