# money_templates/views.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from api import (
    get_templates_by_owner_id,
    get_template_by_id,
    add_template,
    change_template_by_id,
    delete_template_by_id,
    get_active_categories_by_owner_id
)
from utils import validate_percents
import json

money_templates_bp = Blueprint('money_templates', __name__, url_prefix='/money_templates')

def safe_template_by_id(template_id):
    """Возвращает шаблон, если он принадлежит текущему пользователю."""
    t = get_template_by_id(template_id)
    if not t or t[1] != current_user.id:
        return None
    return {
        'template_id': t[0],
        'owner_id': t[1],
        'percents': json.loads(t[2]) if t[2] else {},
        'description': t[3]
    }

@money_templates_bp.route('/')
@login_required
def list_templates():
    raw = get_templates_by_owner_id(current_user.id) or []
    templates = []
    for t in raw:
        try:
            percents = json.loads(t[2])
            percents = {int(k): v for k, v in percents.items()}
        except:
            percents = {}
        templates.append({
            'template_id': t[0],
            'description': t[3],
            'percents': percents
        })
    return render_template('money_templates/list.html', templates=templates)

@money_templates_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    categories = get_active_categories_by_owner_id(current_user.id) or []
    if request.method == 'POST':
        desc = request.form.get('template_description', '').strip()
        if not desc:
            flash("Укажите описание шаблона", "error")
            return redirect(url_for('money_templates.add'))

        percents = {}
        for cat in categories:
            key = f'percent_{cat[0]}'
            val = request.form.get(key)
            if val and val.strip():
                try:
                    v = int(val)
                    if v > 0:
                        percents[cat[0]] = v
                except ValueError:
                    pass

        if not percents:
            flash("Добавьте хотя бы одну категорию", "error")
            return redirect(url_for('money_templates.add'))

        if not validate_percents(percents):
            flash("Сумма процентов должна быть ровно 100%", "error")
            return redirect(url_for('money_templates.add'))

        percents_str = json.dumps({str(k): v for k, v in percents.items()})
        if add_template(owner_id=current_user.id, percents=percents_str, description=desc):
            flash("Шаблон создан", "success")
        else:
            flash("Ошибка: возможно, шаблон с таким описанием уже существует", "error")
        return redirect(url_for('money_templates.list_templates'))

    return render_template('money_templates/add.html', categories=categories)

@money_templates_bp.route('/edit/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit(template_id):
    template = safe_template_by_id(template_id)
    if not template:
        flash("Шаблон не найден", "error")
        return redirect(url_for('money_templates.list_templates'))

    categories = get_active_categories_by_owner_id(current_user.id) or []
    if request.method == 'POST':
        desc = request.form.get('template_description', '').strip()
        if not desc:
            flash("Укажите описание", "error")
            return redirect(url_for('money_templates.edit', template_id=template_id))

        percents = {}
        for cat in categories:
            key = f'percent_{cat[0]}'
            val = request.form.get(key)
            if val and val.strip():
                try:
                    v = int(val)
                    if v > 0:
                        percents[cat[0]] = v
                except ValueError:
                    pass

        if not percents:
            flash("Добавьте хотя бы одну категорию", "error")
            return redirect(url_for('money_templates.edit', template_id=template_id))

        if not validate_percents(percents):
            flash("Сумма процентов должна быть 100%", "error")
            return redirect(url_for('money_templates.edit', template_id=template_id))

        percents_str = json.dumps({str(k): v for k, v in percents.items()})
        if change_template_by_id(id=template_id, percents=percents_str, description=desc):
            flash("Шаблон обновлён", "success")
        else:
            flash("Ошибка при обновлении", "error")
        return redirect(url_for('money_templates.list_templates'))

    return render_template('money_templates/edit.html', template=template, categories=categories)

@money_templates_bp.route('/delete/<int:template_id>', methods=['POST'])
@login_required
def delete(template_id):
    template = safe_template_by_id(template_id)
    if not template:
        flash("Шаблон не найден", "error")
        return redirect(url_for('money_templates.list_templates'))

    if delete_template_by_id(template_id):
        flash("Шаблон удалён", "success")
    else:
        flash("Ошибка при удалении", "error")
    return redirect(url_for('money_templates.list_templates'))