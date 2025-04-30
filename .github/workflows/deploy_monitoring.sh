set -e  # Остановить при ошибке

# Загружаем переменные из .env
export $(grep -v '^#' .env | xargs)

echo "📄 Генерация alertmanager.yml из шаблона"
envsubst < monitoring/alertmanager.yml.template > monitoring/alertmanager.yml

echo "🚀 Перезапуск alertmanager"
docker compose -f docker-compose.monitoring.yaml up -d alertmanager
