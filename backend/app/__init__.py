from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import logging
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_wtf import CSRFProtect

# Инициализация SQLAlchemy
load_dotenv()
db = SQLAlchemy()

logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__, template_folder='templates')
    
    # Настройка логирования
    logging.basicConfig(level=logging.DEBUG)
    
    # Безопасные настройки сессий
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'very-secret-key')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Ограничение размера загружаемых файлов
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB
    
    # Настройка БД
    # Если у вас в .env задана переменная DATABASE_URL = sqlite:///ai_agent.db
    # или другой URL, она будет использована, иначе дефолт ─ файл ai_agent.db
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or 'sqlite:///ai_agent.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Только ваш домен
    CORS(app, origins=["http://127.0.0.1:5000"])
    
    # Разрешаем CORS
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response
    
    # Инициализация БД
    db.init_app(app)
    
    # Подключение CSRFProtect
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Импортируем blueprint после csrf.init_app
    from app.api.routes import api_bp
    app.register_blueprint(api_bp)

    # Отключаем CSRF для всех API маршрутов
    csrf.exempt(api_bp)
    
    with app.app_context():
        db.create_all()  # Создаем таблицы при запуске
    
    return app 