# cards/views.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from api import (
    get_card_by_id,
    get_active_cards_by_owner_id,
    get_active_subcards_by_card_id,
    get_category_by_id,
    add_card,
    delete_card_by_id,
    add_subcard,
    get_subcard_by_card_id_and_category_id,
    get_active_categories_by_owner_id,
    get_inactive_categories_by_owner_id,
    inc_money_to_subcard,
    dec_money_from_subcard,
    transfer_money_between_subcards,
    apply_distribution_to_card,
    collect_category_money_on_one_card,
    delete_category_and_transfer_money_to_new,
    delete_category_and_transfer_money_to_existing,
    get_template_by_id,
    get_templates_by_owner_id,
    get_all_subcards_by_user_id,
    get_transactions
)


from utils import (
    validate_percents,
    card_turple_to_dict,
    card_turples_to_dicts,
    category_turple_to_dict,
    categories_turples_to_dicts
    )
import json

cards_bp = Blueprint('cards', __name__, url_prefix='/cards')



# Вспомогательная функция: проверка принадлежности карты
def ensure_card_ownership(card_id):
    card = get_card_by_id(card_id)
    if not card or card[1] != current_user.id:
        return None
    # card: (id, owner_id, name, amount, is_active, description)
    return card_turple_to_dict(card)


# Вспомогательная функция: получение категории по ID с проверкой владельца
def safe_category_by_id(category_id):
    cat = get_category_by_id(category_id)
    if not cat or cat[1] != current_user.id:
        return None
    return {
        'category_id': cat[0],
        'owner_id': cat[1],
        'category_name': cat[2],
        'amount': cat[3],
        'is_active': cat[4],
        'description': cat[5],
    }

# —————————————————————————————————————
# Основной список карт
# —————————————————————————————————————

@cards_bp.route('/')
@login_required
def list_cards():
    raw_cards = get_active_cards_by_owner_id(current_user.id) or []
    cards = []
    for c in raw_cards:
        cards.append({
            'card_id': c[0],
            'owner_id': c[1],
            'card_name': c[2],
            'amount': c[3],
            'is_active': c[4],
            'description': c[5],
        })
    return render_template('cards/list.html', cards=cards)

# —————————————————————————————————————
# Добавление новой карты
# —————————————————————————————————————

@cards_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('card_name', '').strip()
        desc = request.form.get('description', '').strip()
        if not name:
            flash("Название карты обязательно")
            return redirect(url_for('cards.add'))
        card_id = add_card(owner_id=current_user.id, name=name, description=desc)
        if card_id:
            flash("Карта успешно добавлена")
        else:
            flash("Ошибка: возможно, карта с таким названием уже существует")
        return redirect(url_for('cards.list_cards'))
    return render_template('cards/add.html')

# —————————————————————————————————————
# Управление картой
# —————————————————————————————————————

@cards_bp.route('/<int:card_id>')
@login_required
def manage(card_id):
    card = ensure_card_ownership(card_id)
    if not card:
        flash("Карта не найдена или доступ запрещён")
        return redirect(url_for('cards.list_cards'))
    subcards_raw = get_active_subcards_by_card_id(card_id) or []
    subcards = []
    for sc in subcards_raw:
        cat = safe_category_by_id(sc[2])  # sc[2] = category_id
        subcards.append({
            'subcard_id': sc[0],
            'card_id': sc[1],
            'category_id': sc[2],
            'amount': sc[3],
            'description': sc[4],
            'category_name': cat['category_name'] if cat else f"Категория #{sc[2]} (удалена)",
        })
    return render_template('cards/manage.html', card=card, subcards=subcards)

# —————————————————————————————————————
# Удаление карты
# —————————————————————————————————————

@cards_bp.route('/delete/<int:card_id>', methods=['POST'])
@login_required
def delete(card_id):
    card = ensure_card_ownership(card_id)
    if not card:
        flash("Нет доступа к карте")
        return redirect(url_for('cards.list_cards'))
    if delete_card_by_id(card_id):
        flash("Карта удалена")
    else:
        flash("Не удалось удалить карту")
    return redirect(url_for('cards.list_cards'))

# —————————————————————————————————————
# Привязка категории к карте (создание субкарты)
# —————————————————————————————————————

@cards_bp.route('/<int:card_id>/add_category', methods=['GET', 'POST'])
@login_required
def add_category_to_card(card_id):
    card = ensure_card_ownership(card_id)
    if not card:
        flash("Карта не найдена")
        return redirect(url_for('cards.list_cards'))

    if request.method == 'POST':
        category_id = request.form.get('category_id')
        if not category_id:
            flash("Выберите категорию")
            return redirect(url_for('cards.add_category_to_card', card_id=card_id))
        category_id = int(category_id)
        cat = safe_category_by_id(category_id)
        if not cat:
            flash("Категория не найдена или недоступна")
            return redirect(url_for('cards.add_category_to_card', card_id=card_id))

        # Проверяем, существует ли уже субкарта
        existing = get_subcard_by_card_id_and_category_id(card_id=card_id, category_id=category_id)
        if existing:
            flash("Категория уже привязана к карте")
        else:
            if add_subcard(card_id=card_id, category_id=category_id, description=""):
                flash("Категория добавлена на карту")
            else:
                flash("Ошибка при добавлении")
        return redirect(url_for('cards.manage', card_id=card_id))

    categories_raw = get_active_categories_by_owner_id(current_user.id) or []
    categories = [
        {'category_id': c[0], 'category_name': c[2]}
        for c in categories_raw
    ]
    print(categories)
    return render_template('cards/add_category.html', card=card, categories=categories)

# —————————————————————————————————————
# Пополнение карты — выбор карты → категории → сумма
# —————————————————————————————————————

@cards_bp.route('/add_money')
@login_required
def add_money_step1():
    cards = card_turples_to_dicts(get_active_cards_by_owner_id(current_user.id) or [])
    print("step1:", cards)
    return render_template('cards/add_money_step1.html', cards=cards)

@cards_bp.route('/add_money/<int:card_id>')
@login_required
def add_money_step2(card_id):
    card = ensure_card_ownership(card_id)
    if not card:
        flash("Карта недоступна")
        return redirect(url_for('cards.add_money_step1'))
    subcards_raw = get_active_subcards_by_card_id(card_id) or []
    categories = []
    for sc in subcards_raw:
        cat = safe_category_by_id(sc[2])
        if cat:
            categories.append({
                'category_id': cat['category_id'],
                'category_name': cat['category_name'],
            })
    return render_template('cards/add_money_step2.html', card=card, categories=categories)

@cards_bp.route('/add_money/<int:card_id>/<int:category_id>', methods=['GET', 'POST'])
@login_required
def add_money_step3(card_id, category_id):
    card = ensure_card_ownership(card_id)
    cat = safe_category_by_id(category_id)
    if not card or not cat:
        flash("Недопустимая карта или категория")
        return redirect(url_for('cards.add_money_step1'))

    if request.method == 'POST':
        try:
            amount = int(request.form['money_amount'])
            if amount <= 0:
                raise ValueError()
        except (ValueError, KeyError):
            flash("Укажите корректную сумму")
            return redirect(request.url)

        subcard = get_subcard_by_card_id_and_category_id(card_id=card_id, category_id=category_id)
        if not subcard:
            flash("Субкарта не найдена (внутренняя ошибка)")
            return redirect(url_for('cards.manage', card_id=card_id))

        if inc_money_to_subcard(subcard_id=subcard[0], inc_amount=amount, description="Пополнение"):
            flash(f"На категорию '{cat['category_name']}' зачислено {amount} руб.")
        else:
            flash("Не удалось пополнить счёт")

        return redirect(url_for('cards.manage', card_id=card_id))

    return render_template('cards/add_money_step3.html', card=card, category=cat)

# —————————————————————————————————————
# Списание средств
# —————————————————————————————————————

@cards_bp.route('/dec_money')
@login_required
def dec_money_step1():
    cards = get_active_cards_by_owner_id(current_user.id) or []
    return render_template('cards/dec_money_step1.html', cards=cards)

@cards_bp.route('/dec_money/<int:card_id>')
@login_required
def dec_money_step2(card_id):
    card = ensure_card_ownership(card_id)
    if not card:
        flash("Карта недоступна")
        return redirect(url_for('cards.dec_money_step1'))
    subcards_raw = get_active_subcards_by_card_id(card_id) or []
    categories = []
    for sc in subcards_raw:
        cat = safe_category_by_id(sc[2])
        if cat and sc[3] > 0:  # только если есть деньги
            categories.append({
                'category_id': cat['category_id'],
                'category_name': cat['category_name'],
                'amount': sc[3],
            })
    return render_template('cards/dec_money_step2.html', card=card, categories=categories)

@cards_bp.route('/dec_money/<int:card_id>/<int:category_id>', methods=['GET', 'POST'])
@login_required
def dec_money_step3(card_id, category_id):
    card = ensure_card_ownership(card_id)
    cat = safe_category_by_id(category_id)
    if not card or not cat:
        flash("Недопустимая карта или категория")
        return redirect(url_for('cards.dec_money_step1'))

    subcard = get_subcard_by_card_id_and_category_id(card_id=card_id, category_id=category_id)
    if not subcard or subcard[3] <= 0:
        flash("Недостаточно средств или субкарта неактивна")
        return redirect(url_for('cards.manage', card_id=card_id))

    if request.method == 'POST':
        try:
            amount = int(request.form['money_amount'])
            if amount <= 0 or amount > subcard[3]:
                raise ValueError()
        except (ValueError, KeyError):
            flash("Укажите корректную сумму (не больше баланса)")
            return redirect(request.url)

        if dec_money_from_subcard(subcard_id=subcard[0], dec_amount=amount, description="Списание"):
            flash(f"С категории '{cat['category_name']}' списано {amount} руб.")
        else:
            flash("Не удалось списать средства")

        return redirect(url_for('cards.manage', card_id=card_id))

    return render_template('cards/dec_money_step3.html', card=card, category=cat, balance=subcard[3])

# —————————————————————————————————————
# Перевод между субкартами
# —————————————————————————————————————

@cards_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if request.method == 'POST':
        try:
            card_from = int(request.form['card_from'])
            cat_from = int(request.form['category_from'])
            card_to = int(request.form['card_to'])
            cat_to = int(request.form['category_to'])
            amount = int(request.form['money_amount'])
        except (ValueError, KeyError):
            flash("Некорректные данные")
            return redirect(url_for('cards.transfer'))

        # Проверка принадлежности источника
        if not ensure_card_ownership(card_from):
            flash("Исходная карта не принадлежит вам")
            return redirect(url_for('cards.transfer'))
        if not safe_category_by_id(cat_from):
            flash("Исходная категория недоступна")
            return redirect(url_for('cards.transfer'))

        # Проверка принадлежности получателя
        if not ensure_card_ownership(card_to):
            flash("Целевая карта не принадлежит вам")
            return redirect(url_for('cards.transfer'))
        if not safe_category_by_id(cat_to):
            flash("Целевая категория недоступна")
            return redirect(url_for('cards.transfer'))

        if amount <= 0:
            flash("Сумма должна быть положительной")
            return redirect(url_for('cards.transfer'))

        if transfer_money_between_subcards(
            card_id_from=card_from,
            category_id_from=cat_from,
            card_id_to=card_to,
            category_id_to=cat_to,
            change_amount=amount,
            description="Перевод между субкартами"
        ):
            flash("Перевод выполнен успешно")
        else:
            flash("Не удалось выполнить перевод (недостаточно средств или ошибка)")

        return redirect(url_for('cards.list_cards'))

    # GET — подготовка данных
    cards_raw = get_active_cards_by_owner_id(current_user.id) or []
    cards = [{'card_id': c[0], 'card_name': c[2]} for c in cards_raw]
    categories_raw = get_active_categories_by_owner_id(current_user.id) or []
    categories = [{'category_id': c[0], 'category_name': c[2]} for c in categories_raw]
    
    subcards_raw = get_all_subcards_by_user_id(current_user.id) or []
    subcards = [{'card_id': s[1], 'category_id': s[2]} for s in subcards_raw if s[3]]
    
    category_by_id = {}
    for c in categories:
        category_by_id[c['category_id']] = c
    
    
    print(category_by_id, subcards)

    card_to_categories =  {c['card_id']: [category_by_id[s['category_id']] for s in subcards if s['card_id'] == c['card_id']] for c in cards} 

    all_categories = {}
    all_categories['all'] = categories

    return render_template('cards/transfer.html', cards=cards, categories=categories, card_to_categories=card_to_categories, all_categories=all_categories)

# —————————————————————————————————————
# Зачисление по шаблону
# —————————————————————————————————————

@cards_bp.route('/<int:card_id>/add_by_template', methods=['GET', 'POST'])
@login_required
def add_by_template(card_id):
    card = ensure_card_ownership(card_id)
    if not card:
        flash("Карта недоступна")
        return redirect(url_for('cards.list_cards'))

    templates_raw = get_templates_by_owner_id(current_user.id) or []
    templates = []
    for t in templates_raw:
        templates.append({
            'template_id': t[0],
            'description': t[3],
            'percents': t[2]
        })
    
    categories = categories_turples_to_dicts(get_active_categories_by_owner_id(current_user.id) or [])
    inactive_categories = categories_turples_to_dicts(get_inactive_categories_by_owner_id(current_user.id) or [])
    id_to_category = dict()
    for cat in categories+inactive_categories:
        id_to_category[cat['category_id']] = cat['category_name']

    if request.method == 'POST':
        try:
            template_id = int(request.form['template_id'])
            total_amount = int(request.form['total_amount'])
        except (ValueError, KeyError):
            flash("Некорректные данные")
            return redirect(request.url)

        # Найти шаблон
        template = None
        for t in templates:
            if t['template_id'] == template_id:
                template = t
                break
        if not template:
            flash("Шаблон не найден")
            return redirect(request.url)

        if total_amount <= 0:
            flash("Сумма должна быть положительной")
            return redirect(request.url)

        # Рассчитать распределение
        distributed = {}
        remainder = total_amount
        for cat_id, pct in template['percents'].items():
            if not safe_category_by_id(cat_id):
                continue
            amount = int(total_amount * pct / 100)
            distributed[cat_id] = amount
            remainder -= amount
        # Распределить остаток (до рубля)
        cat_ids = list(distributed.keys())
        if cat_ids and remainder != 0:
            distributed[cat_ids[0]] += remainder

        # Применить распределение
        if apply_distribution_to_card(card_id=card_id, distributed_amounts=distributed):
            flash(f"На карту зачислено {total_amount} руб. по шаблону")
        else:
            flash("Ошибка при зачислении по шаблону")

        return redirect(url_for('cards.manage', card_id=card_id))

    return render_template('cards/add_by_template.html', card=card, templates=templates, id_to_category=id_to_category)

# —————————————————————————————————————
# Сбор денег категории на одну карту
# —————————————————————————————————————

@cards_bp.route('/collect_to_card', methods=['GET', 'POST'])
@login_required
def collect_to_card():
    # Предзагрузка категории из URL (если есть)
    preselected_category_id = request.args.get('category_id')
    if preselected_category_id:
        try:
            preselected_category_id = int(preselected_category_id)
            cat = safe_category_by_id(preselected_category_id)
            if not cat:
                preselected_category_id = None
        except ValueError:
            preselected_category_id = None

    if request.method == 'POST':
        try:
            card_id = int(request.form['card_id'])
            category_id = int(request.form['category_id'])
        except (ValueError, KeyError):
            flash("Некорректные данные", "error")
            return redirect(url_for('cards.collect_to_card'))

        if not ensure_card_ownership(card_id):
            flash("Карта не ваша", "error")
            return redirect(url_for('cards.collect_to_card'))
        if not safe_category_by_id(category_id):
            flash("Категория недоступна", "error")
            return redirect(url_for('cards.collect_to_card'))

        if collect_category_money_on_one_card(card_id=card_id, category_id=category_id):
            flash("Деньги категории собраны на карту", "success")
        else:
            flash("Ошибка при сборе средств", "error")
        return redirect(url_for('cards.list_cards'))

    # GET — подготовка данных
    cards = get_active_cards_by_owner_id(current_user.id) or []
    categories = get_active_categories_by_owner_id(current_user.id) or []
    return render_template(
        'cards/collect_to_card.html',
        cards=[{'card_id': c[0], 'card_name': c[2]} for c in cards],
        categories=[{'category_id': c[0], 'category_name': c[2]} for c in categories],
        preselected_category_id=preselected_category_id
    )
# —————————————————————————————————————
# Удаление категории с переводом средств (на новую)
# —————————————————————————————————————

@cards_bp.route('/delete_category_with_transfer_new/<int:category_id>', methods=['GET', 'POST'])
@login_required
def delete_category_with_transfer_new(category_id):
    cat = safe_category_by_id(category_id)
    if not cat:
        flash("Категория недоступна")
        return redirect(url_for('categories.list_categories'))

    if request.method == 'POST':
        new_name = request.form.get('new_category_name', '').strip()
        new_desc = request.form.get('new_category_description', '').strip()
        if not new_name:
            flash("Укажите название новой категории")
            return redirect(request.url)

        if delete_category_and_transfer_money_to_new(
            old_category_id=category_id,
            new_category_name=new_name,
            new_category_description=new_desc
        ):
            flash("Категория закрыта, средства переведены на новую")
        else:
            flash("Ошибка: возможно, категория с таким названием уже существует")

        return redirect(url_for('categories.list_categories'))

    return render_template('cards/delete_category_new.html', category=cat)

# —————————————————————————————————————
# Удаление категории с переводом средств (на существующую)
# —————————————————————————————————————

@cards_bp.route('/delete_category_with_transfer_existing/<int:category_id>', methods=['GET', 'POST'])
@login_required
def delete_category_with_transfer_existing(category_id):
    cat = safe_category_by_id(category_id)
    if not cat:
        flash("Категория недоступна")
        return redirect(url_for('categories.list_categories'))

    if request.method == 'POST':
        try:
            new_cat_id = int(request.form['category_id'])
        except (ValueError, KeyError):
            flash("Выберите целевую категорию")
            return redirect(request.url)

        if new_cat_id == category_id:
            flash("Нельзя перевести средства в ту же категорию")
            return redirect(request.url)

        if not safe_category_by_id(new_cat_id):
            flash("Целевая категория недоступна")
            return redirect(request.url)

        if delete_category_and_transfer_money_to_existing(
            old_category_id=category_id,
            new_category_id=new_cat_id
        ):
            flash("Категория закрыта, средства переведены")
        else:
            flash("Ошибка при переводе")

        return redirect(url_for('categories.list_categories'))

    categories_raw = get_active_categories_by_owner_id(current_user.id) or []
    categories = [
        {'category_id': c[0], 'category_name': c[2]}
        for c in categories_raw
        if c[0] != category_id  # исключить текущую
    ]
    return render_template('cards/delete_category_existing.html', category=cat, categories=categories)

@cards_bp.app_template_filter('filter_transactions')
def filter_transactions(txs):
    transactions = []
    for tx in txs:
        formatted_date = tx[0].strftime('%d.%m.%Y %H:%M')
        
        new_tx = (formatted_date,) + tx[1:]

        transactions.append(new_tx)
    
    return transactions



from datetime import datetime

from datetime import datetime, timezone, timedelta

@cards_bp.route('/transactions', methods=['GET'])
@login_required
def transactions():
    card_id = request.args.get('card_id', type=int)
    category_id = request.args.get('category_id', type=int)
    time_from_str = request.args.get('time_from')
    time_to_str = request.args.get('time_to')
    tz_offset = request.args.get('tz_offset', type=int)  # в минутах от UTC
    limit = request.args.get('limit', default=50, type=int)
    reverse = request.args.get('reverse') == '1'

    if limit < 1 or limit > 1000:
        limit = 50

    # Функция: локальное время (без TZ) + смещение → UTC
    def local_to_utc(local_dt_str, offset_minutes):
        if not local_dt_str:
            return None
        try:
            naive_dt = datetime.strptime(local_dt_str, '%Y-%m-%dT%H:%M')
            # JS: getTimezoneOffset() = -180 для MSK (UTC+3)
            # Значит, смещение пользователя = -offset_minutes
            user_tz = timezone(timedelta(minutes=-offset_minutes))
            localized = naive_dt.replace(tzinfo=user_tz)
            return localized.astimezone(timezone.utc)
        except ValueError:
            return None

    dt_from = local_to_utc(time_from_str, tz_offset) if tz_offset is not None else None
    dt_to = local_to_utc(time_to_str, tz_offset) if tz_offset is not None else None

    # Если не передан tz_offset — работаем как раньше (naive datetime)
    if tz_offset is None:
        if time_from_str:
            try:
                dt_from = datetime.strptime(time_from_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Некорректное время 'с'", "error")
        if time_to_str:
            try:
                dt_to = datetime.strptime(time_to_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Некорректное время 'по'", "error")

    transactions = []
    if card_id is not None or category_id is not None:
        raw = get_transactions(
            card_id=card_id,
            category_id=category_id,
            time_from=dt_from,
            time_to=dt_to,
            limit=limit,
            reverse=reverse
        )
        if raw is not None:
            transactions = raw
        else:
            flash("Ошибка при загрузке транзакций", "error")

    # Списки для фильтров
    cards = get_active_cards_by_owner_id(current_user.id) or []
    active_cats = get_active_categories_by_owner_id(current_user.id) or []
    inactive_cats = get_inactive_categories_by_owner_id(current_user.id) or []
    all_categories = active_cats + inactive_cats

    # Для отображения в форме: оставляем исходные строки
    return render_template(
        'cards/transactions.html',
        transactions=transactions,
        cards=[{'card_id': c[0], 'card_name': c[2]} for c in cards],
        categories=[{'category_id': c[0], 'category_name': c[2]} for c in all_categories],
        current_card_id=card_id,
        current_category_id=category_id,
        current_time_from=time_from_str or '',
        current_time_to=time_to_str or '',
        current_limit=limit,
        current_reverse=reverse
    )