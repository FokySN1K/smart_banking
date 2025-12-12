# categories/views.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from api import (
    get_active_categories_by_owner_id,
    get_inactive_categories_by_owner_id,
    get_category_by_id,
    add_category,
    change_category_by_id,
    delete_category_by_id,
    reactivate_category_by_id,
    delete_category_and_transfer_money_to_existing,
    transfer_money_to_existing_category,
    transfer_money_to_new_category,
    delete_category_and_transfer_money_to_new
)

from utils import (
    category_turple_to_dict,
    categories_turples_to_dicts
)

from models.user import User



categories_bp = Blueprint('categories', __name__, url_prefix='/categories')



def safe_category_by_id(category_id):
    """Возвращает категорию, если она существует и принадлежит текущему пользователю."""
    cat = get_category_by_id(category_id)
    if not cat or cat[1] != current_user.id:  # cat[1] = owner_id
        return None
    return category_turple_to_dict(cat)


@categories_bp.route('/')
@login_required
def list_categories():
    active = categories_turples_to_dicts(get_active_categories_by_owner_id(current_user.id) or [])
    inactive = categories_turples_to_dicts(get_inactive_categories_by_owner_id(current_user.id) or [])
    return render_template('categories/list.html', active=active, inactive=inactive)

@categories_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['category_name'].strip()
        desc = request.form.get('description', '').strip()
        if not name:
            flash("Название обязательно")
            return redirect(url_for('categories.add'))
        if add_category(owner_id=current_user.id, name=name, description=desc):
            flash("Категория добавлена")
        else:
            flash("Ошибка: возможно, такая категория уже есть")
        return redirect(url_for('categories.list_categories'))
    return render_template('categories/add.html')

@categories_bp.route('/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit(category_id):
    cat = get_category_by_id(category_id)
    if not cat or cat[1] != current_user.id:
        flash("Категория не найдена или доступ запрещён")
        return redirect(url_for('categories.list_categories'))
    if request.method == 'POST':
        name = request.form['category_name'].strip()
        desc = request.form.get('description', '').strip()
        if name and change_category_by_id(id=category_id, name=name, description=desc):
            flash("Категория обновлена")
        return redirect(url_for('categories.list_categories'))
    return render_template('categories/edit.html', category=cat)

@categories_bp.route('/delete/<int:category_id>', methods=['POST'])
@login_required
def delete(category_id):
    cat = get_category_by_id(category_id)
    if not cat or cat[1] != current_user.id:
        flash("Нет доступа")
        return redirect(url_for('categories.list_categories'))
    if category_id == 0:
        flash("Нельзя удалить категорию 'Общее'")
        return redirect(url_for('categories.list_categories'))
    if delete_category_by_id(category_id):
        flash("Категория удалена")
    return redirect(url_for('categories.list_categories'))

@categories_bp.route('/reactivate/<int:category_id>', methods=['POST'])
@login_required
def reactivate(category_id):
    cat = get_category_by_id(category_id)
    if not cat or cat[1] != current_user.id:
        flash("Нет доступа")
        return redirect(url_for('categories.list_categories'))
    if reactivate_category_by_id(category_id):
        flash("Категория восстановлена")
    return redirect(url_for('categories.list_categories'))

# API для AJAX (если нужно)
@categories_bp.route('/api/<int:category_id>')
@login_required
def api_get(category_id):
    cat = get_category_by_id(category_id)
    if not cat or cat[1] != current_user.id:
        return jsonify({}), 403
    return jsonify({
        'category_id': cat[0],
        'owner_id': cat[1],
        'category_name': cat[2],
        'amount': cat[3],
        'is_active': cat[4],
        'description': cat[5]
    })


# categories/views.py

@categories_bp.route('/<int:category_id>/transfer', methods=['GET', 'POST'])
@login_required
def transfer_category(category_id):
    cat = safe_category_by_id(category_id)
    if not cat:
        flash("Категория недоступна", "error")
        return redirect(url_for('categories.list_categories'))

    # Получаем все активные категории (кроме текущей)
    all_cats = get_active_categories_by_owner_id(current_user.id) or []
    other_cats = [c for c in all_cats if c[0] != category_id]

    if request.method == 'POST':
        target_value = request.form.get('target_category_id')
        delete_old = request.form.get('delete_old') == 'on'

        if target_value == 'none':
            flash("Выберите категорию или укажите новую", "error")
            return redirect(request.url)

        if target_value == 'new':
            # Обработка новой категории
            new_name = request.form.get('new_category_name', '').strip()
            new_desc = request.form.get('new_category_description', '').strip()
            if not new_name:
                flash("Укажите название новой категории", "error")
                return redirect(request.url)

            if delete_old:
                success = delete_category_and_transfer_money_to_new(
                    old_category_id=category_id,
                    new_category_name=new_name,
                    new_category_description=new_desc
                )
            else:
                success = transfer_money_to_new_category(
                    old_category_id=category_id,
                    new_category_name=new_name,
                    new_category_description=new_desc
                )

        else:
            # Обработка существующей категории
            try:
                target_id = int(target_value)
            except (ValueError, TypeError):
                flash("Некорректный выбор категории", "error")
                return redirect(request.url)

            if target_id == category_id:
                flash("Нельзя перевести средства в ту же категорию", "error")
                return redirect(request.url)

            if not any(c[0] == target_id for c in other_cats):
                flash("Целевая категория недоступна", "error")
                return redirect(request.url)

            if delete_old:
                success = delete_category_and_transfer_money_to_existing(
                    old_category_id=category_id,
                    new_category_id=target_id
                )
            else:
                success = transfer_money_to_existing_category(
                    old_category_id=category_id,
                    new_category_id=target_id
                )

        if success:
            action = "закрыта и средства переведены" if delete_old else "средства переведены"
            flash(f"Категория обработана: {action}", "success")
        else:
            flash("Ошибка: возможно, категория с таким названием уже существует", "error")

        return redirect(url_for('categories.list_categories'))

    return render_template(
        'categories/transfer.html',
        category=cat,
        other_categories=other_cats
    )