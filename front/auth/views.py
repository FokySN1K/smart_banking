# auth/views.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from api import get_user_by_login, add_user
from utils import hash_password, is_login_exist

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login_name = request.form['login'].strip()
        name = request.form['name'].strip()
        password = request.form['password']

        if len(login_name) > 30:
            flash("Логин не должен превышать 30 символов")
            return redirect(url_for('auth.register'))
        if len(name) > 50:
            flash("Имя не должно превышать 50 символов")
            return redirect(url_for('auth.register'))
        if not login_name or not name or not password:
            flash("Все поля обязательны")
            return redirect(url_for('auth.register'))
        if is_login_exist(login_name):
            flash('Логин уже занят!')
            return redirect(url_for('auth.register'))

        # Генерация соли и хеша
        salt = os.urandom(8).hex()
        password_hash = hash_password(password, salt)
        enc_password = f"{password_hash}:{salt}"

        user_id = add_user(login=login_name, password=enc_password, name=name)
        if user_id:
            flash('Регистрация успешна! Войдите.')
            return redirect(url_for('auth.login'))
        else:
            flash('Ошибка: логин уже существует или другая ошибка.')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_name = request.form['login'].strip()
        password = request.form['password']
        user_data = get_user_by_login(login_name)
        if user_data:
            user = User(*user_data)
            parts = user.password.split(':', 1)
            if len(parts) == 2:
                stored_hash, salt = parts
                if stored_hash == hash_password(password, salt):
                    login_user(user)
                    return redirect(url_for('index'))
        flash('Неверный логин или пароль')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not name or len(name) > 50:
            flash("Имя должно быть от 1 до 50 символов", "error")
            return redirect(url_for('auth.profile'))

        update_data = {'user_id': current_user.id, 'name': name}

        # Обработка смены пароля
        if new_password:
            if len(new_password) < 6:
                flash("Пароль должен быть не короче 6 символов", "error")
                return redirect(url_for('auth.profile'))
            if new_password != confirm_password:
                flash("Пароли не совпадают", "error")
                return redirect(url_for('auth.profile'))

            # Генерация нового хеша
            salt = os.urandom(8).hex()
            password_hash = hash_password(new_password, salt)
            update_data['password'] = f"{password_hash}:{salt}"

        # Вызов API
        from api import change_user_by_id
        if change_user_by_id(**update_data):
            # Обновляем данные в сессии (если имя изменилось)
            current_user.name = name
            flash("Профиль успешно обновлён", "success")
        else:
            flash("Ошибка при обновлении профиля", "error")

        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')