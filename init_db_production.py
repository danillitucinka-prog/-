#!/usr/bin/env python3
"""
Инициализация БД на Vercel/Production
Используется для создания таблиц и тестовых данных
"""

import os
import sys
from app import create_app, db
from models import (
    User, Post, Comment, Subreddit, Message, Notification, 
    Report, Award, UserLog, PostVote, CommentVote, SubredditRule, AutoModFilter
)

def init_production_db():
    """Инициализировать БД в production"""
    
    # Получить окружение (production по умолчанию)
    env = os.environ.get('FLASK_ENV', 'production')
    config_name = 'production' if env == 'production' else 'development'
    
    # Создать приложение
    app = create_app(config_name)
    
    with app.app_context():
        try:
            # Создать все таблицы
            print("🔄 Создание таблиц базы данных...")
            db.create_all()
            print("✓ Таблицы созданы успешно!")
            
            # Проверить, есть ли уже admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("\n👤 Создание admin пользователя...")
                admin = User(
                    username='admin',
                    email='admin@pivoreddit.com',
                    role='admin',
                    is_verified=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✓ Admin создан (admin/admin123)")
            else:
                print("\n✓ Admin уже существует")
            
            # Создать основные сообщества
            print("\n🏘️  Создание стандартных сообществ...")
            communities = [
                ('python', 'Python Programming', 'Обсуждение Python и программирования'),
                ('programming', 'Programming', 'Общее программирование'),
                ('funny', 'Смешное', 'Смешные посты и мемы'),
                ('news', 'Новости', 'Актуальные новости'),
                ('tech', 'Технологии', 'Новости технологий'),
            ]
            
            for name, title, description in communities:
                existing = Subreddit.query.filter_by(name=name).first()
                if not existing:
                    community = Subreddit(
                        name=name,
                        title=title,
                        description=description,
                        moderator_id=admin.id
                    )
                    db.session.add(community)
                    print(f"  ✓ r/{name}")
            
            db.session.commit()
            
            print("\n" + "="*50)
            print("✅ База данных инициализирована успешно!")
            print("="*50)
            print("\n📍 Приложение готово к работе!")
            print("\nДанные для входа:")
            print("  👤 Username: admin")
            print("  🔑 Password: admin123")
            
        except Exception as e:
            print(f"\n❌ Ошибка при инициализации БД:")
            print(f"   {type(e).__name__}: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    init_production_db()
