create table "user"
(
    id            int8          generated always as identity,
    login         varchar(30)   not null,
    password text          not null,
    name          varchar(50)   not null,
    --
    constraint user_id_pk primary key (id),
    constraint user_login_unique unique (login)
);

-- create index
create index user_login_idx on "user" (login);


-- comment
comment on table "user" is 'Таблица пользователей';

comment on column "user".login         is 'Логин пользователя';
comment on column "user".password       is 'Захешированный и посоленный пароль пользователя';
comment on column "user".name          is 'Имя пользователя';
