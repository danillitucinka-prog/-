#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для инициализации приложения и создания тестовых данных
"""

from app import create_app
from models import db, User, Subreddit, Post, Comment
from datetime import datetime, timedelta
import random

def init_database():
    """Инициализация базы данных"""
    app = create_app()
    
    with app.app_context():
        # Удалить все таблицы
        print("🗑️  Очистка базы данных...")
        db.drop_all()
        
        # Создать все таблицы
        print("📊 Создание таблиц базы данных...")
        db.create_all()
        
        # Создать администратора
        print("👤 Создание администратора...")
        admin = User(
            username='admin',
            email='admin@pivoreddit.com',
            role='admin',
            karma=1000,
            is_verified=True,
            level='admin',
            avatar_url='https://www.gravatar.com/avatar/admin?d=identicon'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Создать тестовых пользователей
        print("👥 Создание тестовых пользователей...")
        users = []
        usernames = ['john', 'jane', 'bob', 'alice', 'charlie']
        
        for i, username in enumerate(usernames):
            user = User(
                username=username,
                email=f'{username}@pivoreddit.com',
                role='user' if i % 3 != 0 else 'moderator',
                karma=random.randint(10, 500),
                is_verified=i % 2 == 0,
                level='veteran' if i % 2 == 0 else 'newbie',
                bio=f'Я {username}, рад вас видеть!',
                avatar_url=f'https://www.gravatar.com/avatar/{username}?d=identicon'
            )
            user.set_password('password123')
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        
        # Создать сообщества
        print("🏘️  Создание сообществ...")
        subreddits = []
        subreddit_data = [
            ('python', 'Python Programming', 'Обсуждаем Python и разработку на нем'),
            ('programming', 'Программирование', 'Общее программирование'),
            ('funny', 'Смешное', 'Смешные посты'),
            ('news', 'Новости', 'Последние новости'),
            ('tech', 'Технологии', 'Новости и обсуждение технологий')
        ]
        
        for name, title, description in subreddit_data:
            subreddit = Subreddit(
                name=name,
                title=title,
                description=description,
                moderator_id=users[0].id if users else admin.id,
                member_count=random.randint(50, 500),
                rules='1. Уважайте друг друга\n2. Нет спама\n3. Следите за контентом'
            )
            db.session.add(subreddit)
            subreddits.append(subreddit)
        
        db.session.commit()
        
        # Присоединить пользователей к сообществам
        print("📌 Присоединение пользователей к сообществам...")
        for user in users:
            for subreddit in subreddits[:3]:
                user.join_community(subreddit)
                subreddit.member_count += 1
        
        db.session.commit()
        
        # Создать посты
        print("📝 Создание тестовых постов...")
        posts = []
        titles = [
            'Flask лучше Django? Обсуждаем',
            'Вышел Python 3.12!',
            'Смешные моменты программирования',
            'Новости о Rust 2024',
            'Как начать с машинного обучения?',
            'WebAssembly усовершенствуется',
            'Мой первый проект на Django',
            'Топ 5 баз данных в 2024'
        ]
        
        for i, title in enumerate(titles):
            post = Post(
                title=title,
                content=f'Это интересный пост о {title.lower()}. Обсудим в комментариях!',
                content_type='text',
                author_id=users[i % len(users)].id,
                subreddit_id=subreddits[i % len(subreddits)].id,
                flair='Discussion' if i % 2 == 0 else 'News',
                tags='python,programming' if i % 2 == 0 else 'news,tech',
                upvotes=random.randint(10, 100),
                downvotes=random.randint(0, 10),
                views=random.randint(50, 500),
                is_pinned=i == 0,
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            db.session.add(post)
            posts.append(post)
        
        db.session.commit()
        
        # Создать комментарии
        print("💬 Создание комментариев...")
        comment_texts = [
            'Отличный пост!',
            'Согласен с тобой',
            'Интересная точка зрения',
            'Это не совсем верно',
            'Спасибо за информацию!',
            'Можешь подробнее?'
        ]
        
        for post in posts[:3]:
            for j in range(random.randint(2, 5)):
                comment = Comment(
                    content=comment_texts[j % len(comment_texts)],
                    author_id=users[j % len(users)].id,
                    post_id=post.id,
                    upvotes=random.randint(0, 20),
                    downvotes=random.randint(0, 5)
                )
                db.session.add(comment)
                post.comment_count += 1
        
        db.session.commit()
        
        print("\n✅ База данных успешно инициализирована!")
        print(f"\n📊 Статистика:")
        print(f"   - Пользователей: {User.query.count()}")
        print(f"   - Сообществ: {Subreddit.query.count()}")
        print(f"   - Постов: {Post.query.count()}")
        print(f"   - Комментариев: {Comment.query.count()}")
        
        print(f"\n🔐 Учетные данные администратора:")
        print(f"   - Ник: admin")
        print(f"   - Пароль: admin123")
        
        print(f"\n👥 Тестовые пользователи:")
        for user in users:
            print(f"   - {user.username} / password123")

if __name__ == '__main__':
    init_database()
