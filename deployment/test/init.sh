#!/bin/bash
set -e

# Создание базы данных
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE smart_banking;
EOSQL

# Подключаемся к новой БД и создаём всё остальное
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "smart_banking" <<-EOSQL
    -- Создание владельца
    CREATE USER "$SMART_BANKING_DB_USER" WITH PASSWORD '$SMART_BANKING_DB_PASSWORD';
    ALTER DATABASE smart_banking OWNER TO "$SMART_BANKING_DB_USER";

    -- Роли
    CREATE ROLE dml_role;
    CREATE ROLE read_only_role;

    -- Пользователи приложения
    CREATE USER "$PYTHON_DML_USER" WITH PASSWORD '$PYTHON_DML_PASSWORD';
    CREATE USER "$PYTHON_RO_USER" WITH PASSWORD '$PYTHON_RO_PASSWORD';

    alter role "$PYTHON_DML_USER" set search_path = smart_banking;
    alter role  "$PYTHON_RO_USER" set search_path = smart_banking;

    -- Назначение ролей
    GRANT dml_role TO "$PYTHON_DML_USER";
    GRANT read_only_role TO "$PYTHON_RO_USER";

    -- Схема
    CREATE SCHEMA smart_banking AUTHORIZATION "$SMART_BANKING_DB_USER";

    -- Привилегии
    GRANT CONNECT ON DATABASE smart_banking TO dml_role, read_only_role;
    GRANT USAGE ON SCHEMA smart_banking TO dml_role, read_only_role;

    -- Привилегии по умолчанию
    ALTER DEFAULT PRIVILEGES FOR ROLE "$SMART_BANKING_DB_USER" IN SCHEMA smart_banking
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dml_role;
    ALTER DEFAULT PRIVILEGES FOR ROLE "$SMART_BANKING_DB_USER" IN SCHEMA smart_banking
        GRANT SELECT ON TABLES TO read_only_role;

    -- Последовательности
    ALTER DEFAULT PRIVILEGES FOR ROLE "$SMART_BANKING_DB_USER" IN SCHEMA smart_banking
        GRANT USAGE, SELECT ON SEQUENCES TO dml_role;
    ALTER DEFAULT PRIVILEGES FOR ROLE "$SMART_BANKING_DB_USER" IN SCHEMA smart_banking
        GRANT SELECT ON SEQUENCES TO read_only_role;
EOSQL