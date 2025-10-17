from db import Database
import psycopg2 # для классификации ошибок

MY_API_FOLDER = "sql/"

Database.configure(
    dsn = "postgresql://postgres:postgres@localhost:5432/smart_banking",
    minconn = 1,
    maxconn = 10,
)

def main():
    print_help()

    #create_tables()

    #add_users()
    #get_users()
    #add_cards()

    """
    my_cards = get_active_cards_by_owner_id(get_user_by_login("vovuas2003")[0])
    print("My cards:", my_cards)
    id_to_del = my_cards[0][0]
    ret = delete_card_by_id(id_to_del)
    print("Delete card:", ret)
    my_cards = get_active_cards_by_owner_id(get_user_by_login("vovuas2003")[0])
    print("My cards:", my_cards)
    """

    """
    not_my_cards = get_active_cards_by_owner_id(get_user_by_login("Fokysn1k")[0])
    print("Not my cards:", not_my_cards)
    """

    #drop_tables()

def print_help():
    func = [add_user,
            get_user_by_id,
            get_user_by_login,
            add_card,
            delete_card_by_id,
            get_active_cards_by_owner_id]
    for f in func:
        help(f)
        print()

def create_tables():
    folder = "../migration/src/main/resources/db/tables"
    db = Database.instance()
    # migration/src/main/resources/db/_changelog/create_database_v_1_0.xml
    sequence = ["create_user.sql",
                "create_card.sql",
                "create_category.sql",
                "create_template.sql",
                "create_subcard.sql",
                "create_transaction.sql"]
    for sql in sequence:
        db.execute(folder + "/" + sql)

def drop_tables():
    folder = "../migration/src/main/resources/db/_rollback"
    db = Database.instance()
    db.execute(folder + "/" + "delete_database_v_1_0.sql")

def add_users():
    ret = add_user(login = "vovuas2003", password_hash = "2003", password_salt = "1337", name = "Вова")
    print("Add user vovuas2003:", ret)
    ret = add_user(login = "vovuas2003", password_hash = "any", password_salt = "Mmm...", name = "Хакер")
    print("Add user vovuas2003 (2nd attemp):", ret)
    ret = add_user(login = "Fokysn1k", password_hash = "42", password_salt = "228", name = "Ярик")
    print("Add user Fokysn1k:", ret)

def add_user(**kwargs):
    """
    Добавляет пользователя в БД.
    Аргументы: login, password_hash, password_salt, name (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при ошибке (например, логин занят).
    """
    db = Database.instance()
    try:
        # Вставляем и сразу получаем всю строку
        user_row = db.fetch_one_returning(MY_API_FOLDER + "add_user.sql", params = kwargs)
        return user_row
    except psycopg2.IntegrityError:
        # Логин уже занят (unique constraint)
        return None
    #return None  # Подумать, надо ли здесь этот return на всякий случай, если что-то пошло не так

def get_users():
    ret = get_user_by_id(1)
    print("Get user with id 1:", ret)
    ret = get_user_by_id(2)
    print("Get user with id 2:", ret)
    ret = get_user_by_login("vovuas2003")
    print("Get user vovuas2003:", ret)
    ret = get_user_by_login("Fokysn1k")
    print("Get user Fokysn1k:", ret)
    ret = get_user_by_login("X4k3pM@|-|")
    print("Get user X4k3pM@|-|:", ret)

def get_user_by_id(i):
    """
    Получает пользователя по ID.
    Возвращает строку из БД (кортеж) или None, если не найден.
    """
    db = Database.instance()
    user_row = db.fetch_one(MY_API_FOLDER + "get_user_by_id.sql", params = {'id': i})
    return user_row

def get_user_by_login(login):
    """
    Получает пользователя по логину.
    Возвращает строку из БД (кортеж) или None, если не найден.
    """
    db = Database.instance()
    user_row = db.fetch_one(MY_API_FOLDER + "get_user_by_login.sql", params = {'login': login})
    return user_row

def add_cards():
    i = get_user_by_login("vovuas2003")
    if i is None:
        raise Exception("Cannot find vovuas2003 in database!")
    i = i[0]
    print("vovuas2003 id is", i)
    ret = add_card(owner_id = i, name = "C63p", description = "Основная")
    print("Add card C63p for vovuas2003:", ret)
    ret = add_card(owner_id = i, name = "C63p", description = "Повтор owner_id + name")
    print("Add card C63p for vovuas2003 (2nd attemp):", ret)
    ret = add_card(owner_id = i, name = "Visa", description = "Ненужная")
    print("Add card Visa for vovuas2003:", ret)

def add_card(**kwargs):
    """
    Добавляет карту в БД (is_active всегда True).
    Аргументы: owner_id, name, description (именованные).
    Возвращает строку из БД (кортеж) при успехе или None при конфликте (owner_id + name уже заняты).
    """
    db = Database.instance()
    try:
        card_row = db.fetch_one_returning(MY_API_FOLDER + "add_card.sql", params = kwargs)
        return card_row
    except psycopg2.IntegrityError:
        # Конфликт уникальности owner_id + name
        return None
    # аналогично add_user, подумать про return или другие ошибки

def delete_card_by_id(i):
    """
    Устанавливает is_active = False для карты по ID (мягкое удаление).
    Возвращает обновлённую строку из БД (кортеж) или None, если карта не найдена.
    """
    db = Database.instance()
    card_row = db.fetch_one_returning(MY_API_FOLDER + "delete_card_by_id.sql", params = {'id': i})
    return card_row

def get_active_cards_by_owner_id(owner_id):
    """
    Получает все активные карты пользователя по owner_id.
    Возвращает список строк из БД (кортежей) или пустой список.
    """
    db = Database.instance()
    cards_rows = db.fetch_all(MY_API_FOLDER + "get_active_cards_by_owner_id.sql", params = {'owner_id': owner_id})
    return cards_rows

if __name__ == "__main__":
    main()
