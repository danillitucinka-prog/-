from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import config
from models import db, User, Message
from datetime import datetime

def create_app(config_name='development'):
    """Фабрика приложения"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Инициализация расширений
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в аккаунт'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Создание таблиц
    with app.app_context():
        db.create_all()
    
    # Фильтры для шаблонов
    @app.template_filter('timesince')
    def timesince_filter(dt):
        """Фильтр для отображения времени прошедшего с момента события"""
        if not dt:
            return ''
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 365:
            return f'{diff.days // 365} года назад'
        elif diff.days > 30:
            return f'{diff.days // 30} месяцев назад'
        elif diff.days > 0:
            return f'{diff.days} дней назад'
        elif diff.seconds > 3600:
            return f'{diff.seconds // 3600} часов назад'
        elif diff.seconds > 60:
            return f'{diff.seconds // 60} минут назад'
        else:
            return 'только что'
    
    @app.template_filter('shorten_number')
    def shorten_number_filter(n):
        """Фильтр для сокращения больших чисел"""
        if n >= 1000000:
            return f'{n / 1000000:.1f}M'
        elif n >= 1000:
            return f'{n / 1000:.1f}K'
        return str(n)
    
    # Контекстные процессоры
    @app.context_processor
    def inject_user():
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
        return dict(unread_messages=unread_count)
    
    # Кастомные ошибки
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # blueprints
    from auth import bp as auth_bp
    from users import bp as users_bp
    from posts import bp as posts_bp
    from subreddits import bp as subreddits_bp
    from messages import bp as messages_bp
    from search import bp as search_bp
    from reports import bp as reports_bp
    from admin import bp as admin_bp
    from api import bp as api_bp

    def _alias_blueprint(bp_obj):
        """register blueprint and create unprefixed aliases for its endpoints"""
        app.register_blueprint(bp_obj)
        # iterate over rules after blueprint is registered
        for rule in list(app.url_map.iter_rules()):
            if rule.endpoint.startswith(bp_obj.name + '.'):
                alias = rule.endpoint.split('.', 1)[1]
                if alias not in app.view_functions:
                    app.add_url_rule(
                        rule.rule,
                        endpoint=alias,
                        view_func=app.view_functions[rule.endpoint],
                        methods=rule.methods,
                        defaults=rule.defaults or None,
                    )

    # register all blueprints with aliasing
    for bp_obj in (auth_bp, users_bp, posts_bp, subreddits_bp,
                   messages_bp, search_bp, reports_bp, admin_bp, api_bp):
        _alias_blueprint(bp_obj)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)