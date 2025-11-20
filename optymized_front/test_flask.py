from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)

import hashlib, os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import api

app = Flask(__name__)
app.secret_key = "super_secret_key"

login_manager = LoginManager(app)
login_manager.login_view = "login"



# ----------------------------
#   Пользовательская модель
# ----------------------------

login_limit = 30
name_limit = 50

class User(UserMixin):
    def __init__(self, id, login, password, name):
        self.id = id
        self.login = login
        self.password = password
        self.name = name

    def get_id(self):
        return str(self.id)


# ----------------------------
#   «Базы данных» в памяти
# ----------------------------

users = []

cards_columns = ["card_id", "owner_id", "card_name", "amount", "is_active", "description"]

def turple_cards_to_dict(data):
    return dict(zip(cards_columns, data))

def turples_cards_to_dicts(data):
    return [turple_cards_to_dict(row) for row in data]

cards = [
    {"card_id": 1, "card_number": "1234-5678-9012-3456", "money_amount": 10500, "owner_id": 1, },
    {"card_id": 2, "card_number": "9999-8888-7777-6666", "money_amount": 230, "owner_id": 1},
    {"card_id": 3, "card_number": "5555-4444-3333-2222", "money_amount": 180000, "owner_id": 2}
]




subcards_columns = ["subcard_id", "card_id", "category_id", "amount", "description", "is_active"]

def turple_subcards_to_dict(data):
    return dict(zip(subcards_columns, data))

def turples_subcards_to_dicts(data):
    return [turple_subcards_to_dict(row) for row in data]

subcards = [
    {"card_id": 1, "category_id": 1, "amount": 100},
    {"card_id": 1, "category_id": 2, "amount": 200}

]


books = [
    {"book_name": "Гарри Поттер", "description": "Фэнтези о юном волшебнике."},
    {"book_name": "1984", "description": "Антиутопия о тоталитарном обществе."}
]


categories_columns = ['category_id', 'owner_id', 'category_name', 'amount', 'is_active','description']

def turple_categories_to_dict(data):
    return dict(zip(categories_columns, data))

def turples_categories_to_dicts(data):
    return [turple_categories_to_dict(row) for row in data]

categories = [
    {"category_id": 0, "category_name": "Общее", "owner_id": 1, "description": "1"},
    {"category_id": 1, "category_name": "eda", "owner_id": 1, "description": "2"},
    {"category_id": 2, "category_name": "учеба", "owner_id": 1, "description": "3"}
]


templates_columns = ["template_id", "owner_id", "percents", "description"]

def turple_templates_to_dict(data):
    return dict(zip(templates_columns, data))

def turples_templates_to_dicts(data):
    return [turple_templates_to_dict(row) for row in data]


templates = [
    {"template_id": 1, "owner_id": 1, "percents": {0: 50, 1: 30, 2: 20}, "description":""},
    {"template_id": 2, "owner_id": 1, "percents": {0: 100}, "description":"Мой шаблон"},
    {"template_id": 3, "owner_id": 2, "percents": {0: 70, 1: 30}, "description":""}
]


# ----------------------------
#   Утилиты для хеширования
# ----------------------------

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

# ----------------------------
#              API
# ----------------------------


def user_by_id(user_id):

    data = api.get_user_by_id(user_id)
    print("юзер по id", user_id, data)
    if not data:
        return None
    
    return User(*data)

def add_user_to_db(user):
    users.append(user)

    return user


def create_user(login, name, password):
    salt = os.urandom(8).hex()
    password_hash = hash_password(password, salt)

    enc_password = str(password_hash)+':'+str(salt)

    print("enc_password:", enc_password)

    ret = api.add_user(login=login, password=enc_password, name=name)                     # <<<<<<###############

    print(ret)

    return ret

def is_login_exist(login_name):
    return api.get_user_by_login(login) is not None


def user_by_login(login):
    data = api.get_user_by_login(login)
    print(login, data)

    if not data:
        return None
    
    return User(*data)


def add_category_to_db(new_category):

    data = api.add_category(owner_id=new_category["owner_id"], name=new_category["category_name"], description=new_category["description"])
    print(data)
    categories.append(data)


def user_categories(current_user):
    data = api.get_active_categories_by_owner_id((current_user.id))
    print("Категории юзера", data)
    result = turples_categories_to_dicts(data)
    return result

    #return [{k: v for k, v in c.items() if k not in {"owner_id"}} for c in categories if c["owner_id"] == current_user.id]


def category_by_id(category_id):
    data = api.get_category_by_id(int(category_id))
    if data is None:
        return False
    data = turple_categories_to_dict(data)
    print(data["category_name"])
    return data


@app.route("/category_by_id/<int:category_id>", methods=['GET', 'POST'])
def category_by_id_api(category_id):
    data = turple_categories_to_dict(api.get_category_by_id(int(category_id)))
    print(data["category_name"])
    return jsonify(data)


def inactive_user_catgories(user):
    data = api.get_inactive_categories_by_owner_id(user.id)
    if data is None:
        flash("internal error")
        return None

    return turples_categories_to_dicts(data)


def reactivate_category_api(category_id):
    return api.reactivate_category_by_id(category_id=category_id)


def change_category(category, new_name, new_description):
    api.change_category_by_id(id=category['category_id'], name=new_name, description=new_description)


def delete_category_api(category):
    api.delete_category_by_id(category['category_id'])


def user_cards_api(current_user):
    data = api.get_active_cards_by_owner_id(current_user.id)
    print("Карты юзера", data)
    if data is None:
        flash("internal error")
        return False

    return turples_cards_to_dicts(data)


def subcards_by_card_id(card_id):
    data = api.get_active_subcards_by_card_id(card_id)

    print("сабкарты", data)
    card_subcards = turples_subcards_to_dicts(data)
    print("сабкарты словари", card_subcards)
    return card_subcards


def card_categories_api(card_id):
    data = api.get_active_subcards_by_card_id(card_id)
    card_subcards = turples_subcards_to_dicts(data)
    print("сабкарты словари", card_subcards)
    return [category_by_id(s['category_id']) for s in card_subcards]


def cards_categories_api(user_cards, subcards):
    return {c['card_id']: {category_by_id(s['category_id'])['category_name']: s['money_amount'] for s in subcards if s['card_id'] == c['card_id']} for c in user_cards} 


def card_by_id_api(card_id):
    data = api.get_card_by_id(card_id)
    if data is None:
        flash("internal error")
        return False

    return turple_cards_to_dict(data)


def add_card_api(card_name, description, current_user):
    print("Аргументы новой карты:", card_name, description, current_user.id)
    new_card = api.add_card(owner_id=current_user.id, name=card_name, description=description)
    print("добавленная карта", new_card)
    return new_card


def delete_card_api(card):
    api.delete_card_by_id(card['card_id'])


def add_subcard_api(card_id, category_id, description):
    return api.add_subcard(card_id=card_id, category_id=category_id, description=description)


def subcard_by_card_and_category_id_api(card_id, category_id):
    data = api.get_subcard_by_card_id_and_category_id(card_id=card_id, category_id=category_id)
    return turple_subcards_to_dict(data)


def subcard_balance_inc(subcard, change):
    api.inc_money_to_subcard(subcard_id=subcard['subcard_id'], inc_amount=change, description='')


def subcard_balance_dec(subcard, change):
    api.dec_money_from_subcard(subcard_id=subcard['subcard_id'], dec_amount=change, description='')


def is_subcard_exist(card_id, category_id):
    data = api.get_subcard_by_card_id_and_category_id(card_id, category_id)
    return data is not None


def user_templates_api(current_user):
    data = api.get_templates_by_owner_id(current_user.id)
    print(data)

    data = turples_templates_to_dicts(data)
    return data


def template_by_id_api(template_id):
    data = api.get_template_by_id(template_id)
    print("шаблон по ид\n\n\n\n", template_id, data)
    return turple_templates_to_dict(data)


def add_template_api(percents, current_user, description=""):
    percents = json.dumps({str(k): v for k, v in percents.items()})
    print("проценты", percents)
    new_template = api.add_template(owner_id=current_user.id, percents=percents, description=description)
    print(new_template)
    return new_template


def update_template_api(template, new_percents, template_description):
    data = api.change_template_by_id(id=template['template_id'], percents=json.dumps({str(k): v for k, v in new_percents.items()}), description=template_description)
    print(data)


def delete_template_api(template):
    templates.remove(template)


def validate_percents(percents_dict):
    """Проверяет, что сумма процентов равна 100"""
    return sum(percents_dict.values()) == 100


def transfer_money_between_subcards_api(card_from, category_from, card_to, category_to, money_amount):
    
    data = api.transfer_money_between_subcards(card_id_from=card_from, category_id_from=category_from, card_id_to=card_to, category_id_to=category_to, change_amount=money_amount, description="")
    print(data, card_from, category_from, card_to, category_to, money_amount)
    return data


# ----------------------------
#   Flask-Login callbacks
# ----------------------------

@login_manager.user_loader
def load_user(user_id):
    return user_by_id(user_id)


# ----------------------------
#   РОУТЫ
# ----------------------------


@app.route('/')
def index():
    return render_template('index.html', home=1)

# --- Регистрация ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_name = request.form.get('login')
        name = request.form.get('name')
        password = request.form.get('password')

        if len(login_name) > login_limit:
            flash(f"Логин должен быть не больше {login_limit} символов")
            return redirect(url_for('register'))
        
        if len(name) > name_limit:
            flash(f"Имя должно быть не больше {login_limit} символов")
            return redirect(url_for('register'))

        if is_login_exist(login_name):                   # <<<<<<###############
            flash('Логин уже занят!')
            return redirect(url_for('register'))
        
        res = create_user(login_name, name, password)                  # <<<<<<###############
        
        if res:
            flash('Регистрация прошла успешно! Войдите.')
        else:
            flash('Что-то пошло не так, обратитесь к админу')

        return redirect(url_for('login'))
    return render_template('register.html')

# --- Вход ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_name = request.form.get('login')
        password = request.form.get('password')
        user = user_by_login(login_name)             # <<<<<<###############

        if user is None:
            flash("cannot find user in db")
            return redirect(url_for('login'))


        pswd_hash_and_salt = user.password.split(':')

        if len(pswd_hash_and_salt) != 2:
            flash("wrong structure of user in db, cant resolve")
            return redirect(url_for('login'))

        if user and pswd_hash_and_salt[0] == hash_password(password, pswd_hash_and_salt[1]):
            login_user(user)
            flash('Успешный вход!')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!')
    return render_template('login.html')

# --- Выход ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.')
    return redirect(url_for('login'))


# --- Защищённые страницы ---
# ------------ Категории ------------------------------------------------------------------
@app.route('/categories')
@login_required
def list_categories():

    cur_user_categories = user_categories(current_user)      # <<<<<<###############
    curr_inactive_user_catgories = inactive_user_catgories(current_user)

    return render_template('list_categories.html', title="💳 Ваши категории", items=cur_user_categories, inactive=curr_inactive_user_catgories, base_name='categories', not_visible={"owner_id", "category_id", 'is_active'})



@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        description = request.form.get('description')

        if not category_name:
            flash("Введите название категории.")
            return redirect(url_for('add_category'))

        new_category = {
            "owner_id": current_user.id,
            "category_name": category_name,
            "description": description
        }

        add_category_to_db(new_category)                  # <<<<<<###############
        flash("Категория успешно добавлена!")
        return redirect(url_for('list_categories'))

    return render_template('add_category.html')

@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):

    category = category_by_id(category_id)                    # <<<<<<###############

    if not category:
        return "Категория не найдена", 404

    if category["owner_id"] != current_user.id:
        return "Нет прав для изменения этой категории", 403
    
    if request.method == 'POST':
        new_name = request.form.get('category_name')
        new_description = request.form.get('description')
        if new_name:
            change_category(category, new_name, new_description)            # <<<<<<###############
        flash("Категория обновлёна!")
        return redirect(url_for('list_categories'))

    return render_template('editing_form.html', base_name='categories', category=category)


@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = category_by_id(category_id)                    # <<<<<<###############

    if not category:
        return "Категория не найдена", 404

    if category["owner_id"] != current_user.id:
        return "Нет прав для удаления этой категории", 403
    
    delete_category_api(category)
    flash("Категория удалена.")
    return redirect(url_for('list_categories'))



@app.route('/reactivate_category/<int:category_id>', methods=['POST'])
@login_required
def reactivate_category(category_id):
    category = category_by_id(category_id)                    # <<<<<<###############

    if not category:
        return "Категория не найдена", 404

    if category["owner_id"] != current_user.id:
        return "Нет прав для удаления этой категории", 403

    reactivate_category_api(category['category_id'])
    flash("Категория восстановлена.")
    return redirect(url_for('list_categories'))



@app.route('/books')
@login_required
def list_books():
    return render_template('list.html', title="📚 Список книг", items=books, base_name='books', type="dict")





# ------------ Карты ------------------------------------------------------------------



@app.route('/cards')
@login_required
def list_cards():
    user_cards = user_cards_api(current_user)                     # <<<<<<###############

    #cards_categories = cards_categories_api(user_cards, subcards)  # <<<<<<###############
    return render_template('list_cards.html', title="💳 Ваши карты", items=user_cards, base_name='cards', type="dict", subcards_by_card_id=subcards_by_card_id, category_by_id=category_by_id, not_visible={"owner_id", "card_id", 'is_active'})


@app.route('/edit_card/<int:card_id>', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    card = card_by_id_api(card_id)                            # <<<<<<###############
    if not card:
        return "Карта не найдена", 404
    if request.method == 'POST':
        new_balance = request.form.get('money_amount')
        if new_balance:
            card["money_amount"] = new_balance
        flash("Баланс обновлён!")
        return redirect(url_for('list_cards'))
    return render_template('edit_card.html', base_name='cards', card=card)

@app.route('/delete_card/<int:card_id>', methods=['POST'])
@login_required
def delete_card(card_id):
    card = card_by_id_api(card_id)                    # <<<<<<###############

    if not card:
        return "Карта не найдена", 404

    if card["owner_id"] != current_user.id:
        return "Нет прав для удаления этой карты", 403
    
    delete_card_api(card)
    flash("Карта удалена.")
    return redirect(url_for('list_cards'))

@app.route('/add_category_to_card/<int:card_id>', methods=['GET', 'POST'])
@login_required
def add_category_to_card(card_id):
    card = card_by_id_api(card_id)                             # <<<<<<###############


    if not card:
        return "Карта не найдена", 404
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        print(category_id)
        if category_id:
            category_id = int(category_id)

            if not is_subcard_exist(card_id, category_id):

                add_subcard_api(card["card_id"], category_id, "")                          # <<<<<<###############

            else:
                flash("Категория уже есть на карте")
                return redirect(url_for('list_cards'))


        flash("Категория добавлена!")
        return redirect(url_for('list_cards'))
    return render_template('add_category_to_card.html', base_name='cards', card=card, categories=user_categories(current_user))




@app.route('/add_card', methods=['GET', 'POST'])
@login_required
def add_card():
    if request.method == 'POST':
        card_name = request.form.get('card_name')
        description = request.form.get('description')

        
        new_card = add_card_api(card_name, description, current_user)                                                    # <<<<<<###############

        #add_subcard_api(new_card["card_id"], int(category['category_id']))              # <<<<<<###############

        #print(current_user.id)

        flash("Карта успешно добавлена!")
        return redirect(url_for('list_cards'))

    return render_template('add_card.html', categories=categories)

#------------------- Транзакции ---------------



@app.route('/add_money_general')
@login_required
def add_money_general():
    
    user_cards = user_cards_api(current_user)                             # <<<<<<###############
    
    return render_template('list_for_choice_inc_money.html', title="💳 Ваши карты", items=user_cards, base_name='cards')


@app.route('/add_money_card/<int:card_id>')
@login_required
def add_money_card(card_id):

    card = card_by_id_api(card_id)                                        # <<<<<<###############

    card_categories = card_categories_api(card_id)                           # <<<<<<###############
    
    return render_template('list_for_choice_inc_money.html', title="💳 Ваши категории", items=card_categories, base_name='categories', card=card)



@app.route('/add_money_card_and_category/<int:card_id>/<int:category_id>', methods=['GET', 'POST'])
@login_required
def add_money_card_and_category(card_id, category_id):

    subcard = subcard_by_card_and_category_id_api(card_id, category_id)     # <<<<<<###############

    if request.method == 'POST':
        money_amount = request.form.get('money_amount')

        subcard_balance_inc(subcard, int(money_amount))                       # <<<<<<###############

        flash("Деньги добавлены!")
        return redirect('/')

    return render_template('add_money_card_and_category.html')




@app.route('/dec_money_general')
@login_required
def dec_money_general():
    print("dec money")
    user_cards = user_cards_api(current_user)                             # <<<<<<###############
    
    return render_template('list_for_choice_dec_money.html', title="💳 Ваши карты", items=user_cards, base_name='cards')


@app.route('/dec_money_card/<int:card_id>')
@login_required
def dec_money_card(card_id):

    card = card_by_id_api(card_id)                                        # <<<<<<###############

    card_categories = card_categories_api(card_id)                           # <<<<<<###############
    
    return render_template('list_for_choice_dec_money.html', title="💳 Ваши категории", items=card_categories, base_name='categories', card=card)



@app.route('/dec_money_card_and_category/<int:card_id>/<int:category_id>', methods=['GET', 'POST'])
@login_required
def dec_money_card_and_category(card_id, category_id):


    subcard = subcard_by_card_and_category_id_api(card_id, category_id)     # <<<<<<###############

    if request.method == 'POST':
        money_amount = request.form.get('money_amount')

        subcard_balance_dec(subcard, int(money_amount))                       # <<<<<<###############

        flash("Деньги сняты!")
        return redirect('/')

    return render_template('dec_money_card_and_category.html')


@app.route('/transfer_money_between_subcards', methods=['GET', 'POST'])
@login_required
def transfer_money_between_subcards():

    cards = user_cards_api(current_user)

    card_to_categories = {}
    for card in cards:
        card_to_categories[card['card_id']] = card_categories_api(card['card_id'])

    if request.method == 'POST':
        card_from     = request.form.get('card_from')
        category_from = request.form.get('category_from')
        card_to       = request.form.get('card_to')
        category_to   = request.form.get('category_to')
        money_amount  = request.form.get('money_amount')

        if card_from and category_from and card_to and category_to and money_amount:
            res = transfer_money_between_subcards_api(card_from, category_from, card_to, category_to, int(money_amount))

            if not res:
                flash("some internal error")
            else:
                flash("Деньги преведены!")
        else:
            flash("html error")
        return redirect('/')

    return render_template('transfer_money_between_subcards.html', cards=cards, card_to_categories=card_to_categories)













#------------------- Шаблоны ---------------


# --- Шаблоны распределения ---
@app.route('/templates')
@login_required
def list_templates():
    user_templates = user_templates_api(current_user)
    print(user_templates)
    return render_template('list_of_templates.html', 
                         title="📊 Ваши шаблоны распределения", 
                         items=user_templates, category_by_id=category_by_id)

@app.route('/add_template', methods=['GET', 'POST'])
@login_required
def add_template():
    if request.method == 'POST':
        template_description = request.form.get('template_description')
        
        # Собираем проценты из формы
        percents = {}
        user_cats = user_categories(current_user)
        
        for category in user_cats:
            percent_str = request.form.get(f'percent_{category["category_id"]}')
            if percent_str and percent_str.strip():
                try:
                    percent_val = int(percent_str)
                    if percent_val > 0:
                        percents[category["category_id"]] = percent_val
                except ValueError:
                    pass
        
        # Проверяем валидность
        if not template_description:
            flash("Введите название шаблона.")
            return redirect(url_for('add_template'))
        
        if not percents:
            flash("Добавьте хотя бы одну категорию с процентом.")
            return redirect(url_for('add_template'))
        
        if not validate_percents(percents):
            flash("Сумма процентов должна равняться 100!")
            return redirect(url_for('add_template'))
        
        # Сохраняем шаблон
        add_template_api(percents, current_user, template_description)
        flash("Шаблон успешно добавлен!")
        return redirect(url_for('list_templates'))
    
    user_cats = user_categories(current_user)
    return render_template('add_template.html', 
                         categories=user_cats)

@app.route('/edit_template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    template = template_by_id_api(template_id)
    
    if not template:
        return "Шаблон не найден", 404
    
    if template["owner_id"] != current_user.id:
        return "Нет прав для изменения этого шаблона", 403
    
    if request.method == 'POST':
        template_description = request.form.get('template_description')
        
        # Собираем проценты из формы
        percents = {}
        user_cats = user_categories(current_user)
        
        for category in user_cats:
            percent_str = request.form.get(f'percent_{category["category_id"]}')
            if percent_str and percent_str.strip():
                try:
                    percent_val = int(percent_str)
                    if percent_val > 0:
                        percents[category["category_id"]] = percent_val
                except ValueError:
                    pass
        
        # Проверяем валидность
        if not template_description:
            flash("Введите название шаблона.")
            return redirect(url_for('edit_template', template_id=template_id))
        
        if not percents:
            flash("Добавьте хотя бы одну категорию с процентом.")
            return redirect(url_for('edit_template', template_id=template_id))
        
        if not validate_percents(percents):
            flash("Сумма процентов должна равняться 100!")
            return redirect(url_for('edit_template', template_id=template_id))
        
        # Обновляем шаблон
        update_template_api(template, percents, template_description)
        flash("Шаблон успешно обновлен!")
        return redirect(url_for('list_templates'))
    
    user_cats = user_categories(current_user)
    return render_template('edit_template.html', 
                         template=template, 
                         categories=user_cats)

@app.route('/delete_template/<int:template_id>', methods=['POST'])
@login_required
def delete_template(template_id):
    template = template_by_id_api(template_id)
    
    if not template:
        return "Шаблон не найден", 404
    
    if template["owner_id"] != current_user.id:
        return "Нет прав для удаления этого шаблона", 403
    
    delete_template_api(template)
    flash("Шаблон удален.")
    return redirect(url_for('list_templates'))


@app.route('/add_money_by_template/<int:card_id>', methods=['GET', 'POST'])
@login_required
def add_money_by_template(card_id):
    card = card_by_id_api(card_id)

    print(card)

    if not card:
        return "Карта не найдена", 404

    if card["owner_id"] != current_user.id:
        return "Нет прав для доступа к этой карте", 403

    if request.method == 'POST':
        template_id = request.form.get('template_id')
        total_amount_str = request.form.get('total_amount')

        if not template_id or not total_amount_str:
            flash("Выберите шаблон и укажите сумму")
            return redirect(url_for('add_money_by_template', card_id=card_id))

        try:
            template_id = int(template_id)
            total_amount = int(total_amount_str)
        except ValueError:
            flash("Некорректные данные")
            return redirect(url_for('add_money_by_template', card_id=card_id))

        template = template_by_id_api(template_id)

        if not template:
            flash("Шаблон не найден")
            return redirect(url_for('add_money_by_template', card_id=card_id))

        if template["owner_id"] != current_user.id:
            flash("Нет прав для использования этого шаблона")
            return redirect(url_for('add_money_by_template', card_id=card_id))

        # 🧮 Собираем фактическое распределение из формы
        distributed_amounts = {}
        total_from_form = 0

        for category_id in template["percents"].keys():
            form_key = f"category_amount_{category_id}"
            
            if form_key in request.form:
                try:
                    amount_for_category = int(request.form[form_key])
                except ValueError:
                    amount_for_category = 0
                distributed_amounts[category_id] = amount_for_category
                total_from_form += amount_for_category

        # ⚠️ Проверяем совпадение общей суммы (не обязательно, но полезно)
        if total_from_form != total_amount:
            flash(f"Внимание: сумма по категориям ({total_from_form} руб.) не совпадает с общей ({total_amount} руб.)")
            total_amount = total_from_form  # можно скорректировать, либо оставить

        # 🏦 Обновляем субкарты и баланс
        res = api.apply_distribution_to_card(card['card_id'], distributed_amounts)

        if res:
            # 🧾 Формируем сообщение о распределении
            distribution_info = []
            for category_id, amount in distributed_amounts.items():
                category = category_by_id(category_id)
                category_name = category["category_name"] if category else f"Категория {category_id}"
                distribution_info.append(f"{category_name}: {amount} руб.")

            flash(
                f"На карту зачислено {total_amount} руб. по шаблону #{template['template_id']}. "
                f"Распределение: {', '.join(distribution_info)}"
            )
        else:
            flash("Что-то пошло не так!!!!!!!!")

        return redirect(url_for('list_cards'))

    # GET-запрос: показать форму
    user_templates = user_templates_api(current_user)
    print(card, user_templates)
    return render_template(
        'add_money_to_card_by_template.html',
        card=card,
        templates=user_templates,
        category_by_id=category_by_id)


















if __name__ == '__main__':
    app.run(debug=True, port=5001)
