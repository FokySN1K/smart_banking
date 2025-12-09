# app.py
import os
from flask import Flask, render_template
from flask_login import LoginManager
from dotenv import load_dotenv
from models.user import User

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import api

from money_templates.views import money_templates_bp
from api import get_user_by_id

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        data = get_user_by_id(int(user_id))
        return User(*data) if data else None

    # Blueprints
    from auth.views import auth_bp
    from categories.views import categories_bp
    from cards.views import cards_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(money_templates_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=True)