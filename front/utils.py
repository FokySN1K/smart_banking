# utils.py
import hashlib
import os

def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode()).hexdigest()

def is_login_exist(login: str) -> bool:
    from api import get_user_by_login
    return get_user_by_login(login) is not None

def validate_percents(percents_dict: dict) -> bool:
    """Проверяет, что сумма процентов равна 100."""
    if not percents_dict:
        return False
    return sum(percents_dict.values()) == 100


categories_columns = ['category_id', 'owner_id', 'category_name', 'amount', 'is_active','description']

def category_turple_to_dict(category):
    return {
        'category_id': category[0],
        'owner_id': category[1],
        'category_name': category[2],
        'amount': category[3],
        'is_active': category[4],
        'description': category[5],
    }

def categories_turples_to_dicts(categories):
    result = []

    for category in categories:
        result.append(category_turple_to_dict(category))
    
    return result

cards_columns = ["card_id", "owner_id", "card_name", "amount", "is_active", "description"]

def card_turple_to_dict(card):
    return {
        'card_id': card[0],
        'owner_id': card[1],
        'card_name': card[2],
        'amount': card[3],
        'is_active': card[4],
        'description': card[5],
    }

def card_turples_to_dicts(cards):
    result = []

    for card in cards:
        result.append(card_turple_to_dict(card))
    
    return result
