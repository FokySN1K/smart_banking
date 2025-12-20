#!/bin/bash

# Загружаем переменные из .env (игнорируем комментарии и пустые строки)
if [ ! -f .env ]; then
  echo ".env не найден в текущей директории!"
  exit 1
fi

# Экспортируем все переменные из .env
set -a
source .env
set +a

cat > ../../migration/liquibase.properties <<EOF
url=jdbc:postgresql://localhost:${DB_PORT}/smart_banking
username=${SMART_BANKING_DB_USER}
password=${SMART_BANKING_DB_PASSWORD}
EOF

cat > ../../api/python.env <<EOF
PYTHON_DML_USER=${PYTHON_DML_USER}
PYTHON_DML_PASSWORD=${PYTHON_DML_PASSWORD}
DB_HOST=localhost
DB_PORT=${DB_PORT}
EOF

echo "liquibase.properties успешно создан в /migration/"