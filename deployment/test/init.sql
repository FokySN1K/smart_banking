-- Создание базы данных
create database smart_banking;

-- Создание пользователя-владельца
create user smart_banking with password 'smart_banking';

-- Назначение владельца базы данных
alter database smart_banking owner to smart_banking;

-- Создание ролей
create role dml_role;
create role read_only_role;

-- Создание пользователей приложения
create user python_smart_banking_dml with password 'python_smart_banking_dml';
create user python_smart_banking_ro with password 'python_smart_banking_ro';

-- Назначение ролей пользователям
grant dml_role to python_smart_banking_dml;
grant read_only_role to python_smart_banking_ro;

-- Подключение к целевой базе данных
\c smart_banking

-- Создание схемы
create schema smart_banking authorization smart_banking;

-- Предоставление привилегий на подключение
grant connect on database smart_banking to dml_role, read_only_role;

-- Предоставление привилегий на использование схемы
grant usage on schema smart_banking to dml_role, read_only_role;

-- Предоставление привилегий по умолчанию для будущих таблиц
alter default privileges in schema smart_banking grant select, insert, update, delete on tables to dml_role;
alter default privileges in schema smart_banking grant select on tables to read_only_role;

-- Предоставление привилегий на последовательности (для автоинкрементных полей)
alter default privileges in schema smart_banking grant usage, select on sequences to dml_role;
alter default privileges in schema smart_banking grant select on sequences to read_only_role;