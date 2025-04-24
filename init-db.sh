#!/bin/bash

# Останавливаем все контейнеры
docker-compose down

# Удаляем все тома
docker volume prune -f

# Запускаем контейнеры
docker-compose up -d

# Ждем, пока база данных будет готова
sleep 10

# Создаем таблицы
docker-compose exec web alembic upgrade head

echo "База данных успешно инициализирована!" 