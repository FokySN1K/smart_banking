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