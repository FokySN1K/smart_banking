from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)

import hashlib, os

app = Flask(__name__)
app.secret_key = "super_secret_key"

login_manager = LoginManager(app)
login_manager.login_view = "login"

# ----------------------------
#   «Базы данных» в памяти
# ----------------------------

users = []

cards = [
    {"card_id": 1, "card_number": "1234-5678-9012-3456", "money_amount": 10500, "owner_id": 1, },
    {"card_id": 2, "card_number": "9999-8888-7777-6666", "money_amount": 230, "owner_id": 1},
    {"card_id": 3, "card_number": "5555-4444-3333-2222", "money_amount": 180000, "owner_id": 2}
]

subcards = [
    {"card_id": 1, "category_id": 1, "money_amount": 100},
    {"card_id": 1, "category_id": 2, "money_amount": 200}

]


books = [
    {"book_name": "Гарри Поттер", "description": "Фэнтези о юном волшебнике."},
    {"book_name": "1984", "description": "Антиутопия о тоталитарном обществе."}
]


general_category = "Общее"
categories = [
    {"category_id": 0, "category_name": general_category, "owner_id": 1},
    {"category_id": 1, "category_name": "eda", "owner_id": 1},
    {"category_id": 2, "category_name": "учеба", "owner_id": 1}
]


# ----------------------------
#   Пользовательская модель
# ----------------------------

login_limit = 30
name_limit = 50

class User(UserMixin):
    def __init__(self, id, login, name, password_hash, salt):
        self.id = id
        self.login = login
        self.name = name
        self.password_hash = password_hash
        self.salt = salt

    def get_id(self):
        return str(self.id)

# ----------------------------
#   Flask-Login callbacks
# ----------------------------

@login_manager.user_loader
def load_user(user_id):
    for u in users:
        if u.id == int(user_id):
            return u
    return None

# ----------------------------
#   Утилиты для хеширования
# ----------------------------

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def create_user(login, password):
    salt = os.urandom(8).hex()
    password_hash = hash_password(password, salt)
    user = User(id=len(users) + 1, login=login, password_hash=password_hash, salt=salt)
    users.append(user)
    
    return user

# ----------------------------
#   РОУТЫ
# ----------------------------

def is_user_exist(login):
    cur.execute(sql_query, params)

@app.route('/')
def index():
    return render_template('index.html', home=1)

# --- Регистрация ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_name = request.form.get('login')
        password = request.form.get('password')

        if len(login_name) > login_limit:
            flash(f"Логин должен быть не больше {login_limit} символов")
            return redirect(url_for('register'))


        if any(u.login == login_name for u in users):
            flash('Логин уже занят!')
            return redirect(url_for('register'))
        create_user(login_name, password)
        flash('Регистрация прошла успешно! Войдите.')
        return redirect(url_for('login'))
    return render_template('register.html')

# --- Вход ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_name = request.form.get('login')
        password = request.form.get('password')
        user = next((u for u in users if u.login == login_name), None)
        if user and user.password_hash == hash_password(password, user.salt):
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
@app.route('/categories')
@login_required
def list_categories():
    general_exist = False
    for c in categories:
        if (c['category_name'] == general_category and c['owner_id'] == current_user.id):
            general_exist = True

    if not general_exist:
        new_category = {
            "category_id": len(categories)+1,
            "category_name": general_category,
            "owner_id": current_user.id
        }
        categories.append(new_category)

    user_categories = [{k: v for k, v in c.items() if k not in {"owner_id"}} for c in categories if c["owner_id"] == current_user.id]

    return render_template('list.html', title="💳 Ваши категории", items=user_categories, base_name='categories', type="list", arg="category_name")


# ------------ Категории ------------------------------------------------------------------

@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        category_name = request.form.get('category_name')

        if not category_name:
            flash("Введите название категории.")
            return redirect(url_for('add_category'))

        new_category = {
            "category_id": len(categories)+1,
            "category_name": category_name,
            "owner_id": current_user.id
        }
        print(current_user.id)
        categories.append(new_category)
        flash("Категория успешно добавлена!")
        return redirect(url_for('list_categories'))

    return render_template('add_category.html')

@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):

    category = next((c for c in categories if c["category_id"] == category_id), None)

    if not category:
        return "Категория не найдена", 404
    if request.method == 'POST':
        new_name = request.form.get('category_name')
        if new_name:
            category["category_name"] = new_name
        flash("Имя обновлёно!")
        return redirect(url_for('list_categories'))

    return render_template('editing_form.html', base_name='categories', category=category)


@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = next((c for c in categories if c["category_id"] == category_id), None)
    if not category:
        return "Категория не найдена", 404

    if category["owner_id"] != current_user.id:
        return "Нет прав для удаления этой категории", 403

    categories.remove(category)
    flash("Категория удалена.")
    return redirect(url_for('list_categories'))





@app.route('/books')
@login_required
def list_books():
    return render_template('list.html', title="📚 Список книг", items=books, base_name='books', type="dict")





# ------------ Карты ------------------------------------------------------------------


def category_by_id(category_id):
    category = None

    for cat in categories:
        if cat['category_id'] == category_id:
            category = cat

    if category:
        return category

    return category


@app.route('/cards')
@login_required
def list_cards():
    user_cards = [{k: v for k, v in c.items() if k} for c in cards if c["owner_id"] == current_user.id]

    cards_categories = {c['card_id']: {category_by_id(s['category_id'])['category_name']: s['money_amount'] for s in subcards if s['card_id'] == c['card_id']} for c in user_cards} 
    return render_template('list.html', title="💳 Ваши карты", items=user_cards, base_name='cards', type="dict", cards_categories=cards_categories, not_visible={"owner_id", "card_id"})


@app.route('/edit_card/<card_number>', methods=['GET', 'POST'])
@login_required
def edit_card(card_number):
    card = next((c for c in cards if c["card_number"] == card_number), None)
    if not card:
        return "Карта не найдена", 404
    if request.method == 'POST':
        new_balance = request.form.get('money_amount')
        if new_balance:
            card["money_amount"] = new_balance
        flash("Баланс обновлён!")
        return redirect(url_for('list_cards'))
    return render_template('edit_card.html', base_name='cards', card=card)


@app.route('/add_category_to_card/<card_number>', methods=['GET', 'POST'])
@login_required
def add_category_to_card(card_number):
    card = next((c for c in cards if c["card_number"] == card_number), None)


    if not card:
        return "Карта не найдена", 404
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        if category_id:

            new_subcard = {
                "card_id": card["card_id"], 
                "category_id": int(category_id), 
                "money_amount": 0
            }

            subcards.append(new_subcard)
        flash("Категория добавлена!")
        return redirect(url_for('list_cards'))
    return render_template('add_category_to_card.html', base_name='cards', card=card, categories=categories)


def max_card_id():
    id = 0
    for c in cards:
        if c["card_id"] > id:
            id = c["card_id"]
    return id

@app.route('/add_card', methods=['GET', 'POST'])
@login_required
def add_card():
    if request.method == 'POST':
        card_number = request.form.get('card_number')
        money_amount = request.form.get('money_amount')

#        category_id = request.form.get('category_id')

        new_card = {
            "card_id": max_card_id()+1,
            "card_number": card_number,
            "money_amount": int(money_amount),
            "owner_id": current_user.id
        }

        category = next((c for c in categories if c["owner_id"] == current_user.id and c["category_name"] == general_category), None)
        new_subcard = {
            "card_id": new_card["card_id"],
            "category_id": int(category['category_id']),
            "money_amount": 0
        }
        subcards.append(new_subcard)


        print(current_user.id)
        cards.append(new_card)
        flash("Карта успешно добавлена!")
        return redirect(url_for('list_cards'))

    return render_template('add_card.html', categories=categories)

#------------------- Транзакции ---------------



@app.route('/add_money_general')
@login_required
def add_money_general():
    
    user_cards = [{k: v for k, v in c.items() if k} for c in cards if c["owner_id"] == current_user.id]
    
    return render_template('list_for_choice.html', title="💳 Ваши карты", items=user_cards, base_name='cards')


@app.route('/add_money_card/<int:card_id>')
@login_required
def add_money_card(card_id):

    card =  next((c for c in cards if c["card_id"] == card_id), None)

    card_categories = [category_by_id(s['category_id']) for s in subcards if s['card_id'] == card_id]
    
    return render_template('list_for_choice.html', title="💳 Ваши категории", items=card_categories, base_name='categories', card=card)



@app.route('/add_money_card_and_category/<int:card_id>/<int:category_id>', methods=['GET', 'POST'])
@login_required
def add_money_card_and_category(card_id, category_id):

    card =  next((c for c in cards if c["card_id"] == card_id), None)

    subcard = next((s for s in subcards if s["card_id"] == card_id and s["category_id"] == category_id), None)

    if request.method == 'POST':
        money_amount = request.form.get('money_amount')
        
        subcard['money_amount'] += int(money_amount)
        card['money_amount'] += int(money_amount)

        flash("Деньги добавлены!")
        return redirect('/')

    return render_template('add_money_card_and_category.html')






if __name__ == '__main__':
    app.run(debug=True, port=5001)
