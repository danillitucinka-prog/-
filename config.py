import os
from datetime import timedelta

class Config:
    """Базовая конфигурация приложения"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Поддержка PostgreSQL для Vercel/Production и SQLite для локальной разработки
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Для Vercel/Production используем PostgreSQL
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Для локальной разработки используем SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # True в продакшене
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Пагинация
    POSTS_PER_PAGE = 20
    COMMENTS_PER_PAGE = 10
    USERS_PER_PAGE = 20
    
    # Загрузка файлов
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Спам-защита
    POST_COOLDOWN_SECONDS = 60  # 1 минута между постами
    COMMENT_COOLDOWN_SECONDS = 10  # 10 секунд между комментариями
    
    # Настройки
    DEFAULT_LANGUAGE = 'ru'
    DARK_MODE_DEFAULT = False

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
