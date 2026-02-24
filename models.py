from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

# Таблица связи для подписок на юзеров
user_followers = db.Table(
    'user_followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('following_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Таблица связи для подписок на сообщества
user_subreddits = db.Table(
    'user_subreddits',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('subreddit_id', db.Integer, db.ForeignKey('subreddit.id'), primary_key=True)
)

# Таблица связи для избранного
saved_posts = db.Table(
    'saved_posts',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)

# Таблица связи для блокировок
blocked_users = db.Table(
    'blocked_users',
    db.Column('blocker_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('blocked_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """Модель пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(500), default='https://www.gravatar.com/avatar/default')
    bio = db.Column(db.Text, default='')
    is_verified = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    is_online = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')  # user, moderator, admin
    
    # Карма и уровень
    karma = db.Column(db.Integer, default=0)
    level = db.Column(db.String(20), default='newbie')  # newbie, veteran, etc
    
    # Даты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Настройки приватности (JSON)
    privacy_settings = db.Column(db.Text, default='{}')
    language = db.Column(db.String(5), default='ru')
    dark_mode = db.Column(db.Boolean, default=False)
    
    # Vztahy
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')
    post_votes = db.relationship('PostVote', backref='user', lazy=True, cascade='all, delete-orphan')
    comment_votes = db.relationship('CommentVote', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # Подписки
    following = db.relationship('User', secondary=user_followers,
                                primaryjoin=(id == user_followers.c.follower_id),
                                secondaryjoin=(id == user_followers.c.following_id),
                                backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    
    # Сообщества
    communities = db.relationship('Subreddit', secondary=user_subreddits,
                                  backref=db.backref('members', lazy='dynamic'), lazy='dynamic')
    
    # Модерируемые сообщества
    moderated_subreddits = db.relationship('Subreddit', backref='moderator_user', lazy=True)
    
    # Избранное
    saved = db.relationship('Post', secondary=saved_posts, lazy='dynamic')
    
    # Блокировки
    blocking = db.relationship('User', secondary=blocked_users,
                              primaryjoin=(id == blocked_users.c.blocker_id),
                              secondaryjoin=(id == blocked_users.c.blocked_id),
                              backref=db.backref('blocked_by', lazy='dynamic'), lazy='dynamic')
    
    # ЛС
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', 
                                   backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id',
                                       backref='recipient', lazy=True)
    
    # Награды
    given_awards = db.relationship('Award', backref='giver', lazy=True)
    
    # Уведомления
    notifications = db.relationship('Notification', backref='user', lazy=True,
                                   cascade='all, delete-orphan')
    
    # Логи
    logs = db.relationship('UserLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # Отчеты
    reports = db.relationship('Report', backref='reporter', lazy=True)

    def set_password(self, password):
        """Установить пароль с хешированием"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверить пароль"""
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        """Подписаться на пользователя"""
        if not self.is_following(user):
            self.following.append(user)

    def unfollow(self, user):
        """Отписаться от пользователя"""
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        """Проверить статус подписки"""
        return self.following.filter_by(id=user.id).first() is not None

    def join_community(self, subreddit):
        """Вступить в сообщество"""
        if subreddit not in self.communities:
            self.communities.append(subreddit)

    def leave_community(self, subreddit):
        """Выход из сообщества"""
        if subreddit in self.communities:
            self.communities.remove(subreddit)

    def is_in_community(self, subreddit):
        """Проверить членство"""
        return subreddit in self.communities

    def block_user(self, user):
        """Заблокировать пользователя"""
        if not self.is_blocking(user):
            self.blocking.append(user)

    def unblock_user(self, user):
        """Разблокировать пользователя"""
        if self.is_blocking(user):
            self.blocking.remove(user)

    def is_blocking(self, user):
        """Проверить блокировку"""
        return self.blocking.filter_by(id=user.id).first() is not None

    def save_post(self, post):
        """Сохранить пост в избранное"""
        if post not in self.saved:
            self.saved.append(post)
            db.session.commit()

    def unsave_post(self, post):
        """Удалить пост из избранного"""
        if post in self.saved:
            self.saved.remove(post)
            db.session.commit()

    def is_post_saved(self, post):
        """Проверить сохранен ли пост"""
        return self.saved.filter_by(id=post.id).first() is not None

    def get_privacy_settings(self):
        """Получить настройки приватности"""
        try:
            return json.loads(self.privacy_settings) if self.privacy_settings else {}
        except:
            return {}

    def set_privacy_settings(self, settings):
        """Установить настройки приватности"""
        self.privacy_settings = json.dumps(settings)

    def add_log(self, action, details=''):
        """Добавить запись в лог"""
        log = UserLog(user_id=self.id, action=action, details=details)
        db.session.add(log)

    def __repr__(self):
        return f'<User {self.username}>'


class Subreddit(db.Model):
    """Модель сообщества (сабреддита)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    rules = db.Column(db.Text, default='')
    icon_url = db.Column(db.String(500), default='')
    banner_url = db.Column(db.String(500), default='')
    
    is_private = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    
    moderator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    member_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Vztahy
    posts = db.relationship('Post', backref='subreddit', lazy=True, cascade='all, delete-orphan')
    rules_list = db.relationship('SubredditRule', backref='subreddit', lazy=True,
                                cascade='all, delete-orphan')
    filters = db.relationship('AutoModFilter', backref='subreddit', lazy=True,
                             cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Subreddit r/{self.name}>'


class SubredditRule(db.Model):
    """Правило сообщества"""
    id = db.Column(db.Integer, primary_key=True)
    subreddit_id = db.Column(db.Integer, db.ForeignKey('subreddit.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')


class Post(db.Model):
    """Модель поста"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False, index=True)
    content = db.Column(db.Text, default='')
    content_type = db.Column(db.String(20), default='text')  # text, link, image
    
    # URL для ссылок/картинок
    url = db.Column(db.String(500), default='')
    preview_image = db.Column(db.String(500), default='')
    
    # Markdown поддержка
    is_markdown = db.Column(db.Boolean, default=True)
    
    # Теги и флейры
    flair = db.Column(db.String(50), default='')
    tags = db.Column(db.String(200), default='')  # comma-separated
    
    # Состояние поста
    is_pinned = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Счетчики
    views = db.Column(db.Integer, default=0)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    # Иностранные ключи
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    subreddit_id = db.Column(db.Integer, db.ForeignKey('subreddit.id'), nullable=False, index=True)
    
    # Даты
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Vztahy
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('PostVote', backref='post', lazy=True, cascade='all, delete-orphan')
    awards = db.relationship('Award', backref='post', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='post', lazy=True, cascade='all, delete-orphan')

    def get_net_votes(self):
        """Получить разницу лайков и дизлайков"""
        return self.upvotes - self.downvotes

    def get_preview_text(self, length=150):
        """Получить предпросмотр текста"""
        if self.content:
            return self.content[:length] + ('...' if len(self.content) > length else '')
        return ''

    def increment_views(self):
        """Увеличить счетчик просмотров"""
        self.views += 1
        db.session.commit()

    def __repr__(self):
        return f'<Post {self.title[:50]} by {self.author.username}>'


class Comment(db.Model):
    """Модель комментария"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Состояние
    is_deleted = db.Column(db.Boolean, default=False)
    is_edited = db.Column(db.Boolean, default=False)
    
    # Счетчики
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    
    # Иностранные ключи
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), default=None)
    
    # Даты
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Vztahy
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                             lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('CommentVote', backref='comment', lazy=True, cascade='all, delete-orphan')
    awards = db.relationship('Award', foreign_keys='Award.comment_id', 
                            backref='comment', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='comment', lazy=True, cascade='all, delete-orphan')

    def get_net_votes(self):
        """Получить разницу лайков и дизлайков"""
        return self.upvotes - self.downvotes

    def __repr__(self):
        return f'<Comment by {self.author.username} on post {self.post_id}>'


class PostVote(db.Model):
    """Модель голоса за пост"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    vote_type = db.Column(db.String(10), nullable=False)  # upvote, downvote
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_post_vote'),)


class CommentVote(db.Model):
    """Модель голоса за комментарий"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False, index=True)
    vote_type = db.Column(db.String(10), nullable=False)  # upvote, downvote
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_comment_vote'),)


class Award(db.Model):
    """Модель награды"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon_url = db.Column(db.String(500), default='')
    description = db.Column(db.Text, default='')
    
    giver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), default=None)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), default=None)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    """Модель личного сообщения"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    subject = db.Column(db.String(100), default='')
    content = db.Column(db.Text, nullable=False)
    
    is_read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (db.Index('idx_message_recipient_read', 'recipient_id', 'is_read'),)


class Notification(db.Model):
    """Модель уведомления"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    notification_type = db.Column(db.String(20), nullable=False)  # reply, mention, follow, award
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    link = db.Column(db.String(500), default='')
    
    is_read = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (db.Index('idx_notification_user_read', 'user_id', 'is_read'),)


class Report(db.Model):
    """Модель отчета о нарушении"""
    id = db.Column(db.Integer, primary_key=True)
    
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), default=None)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), default=None)
    
    reason = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, dismissed, acted
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class UserLog(db.Model):
    """Лог действий пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, default='')
    ip_address = db.Column(db.String(50), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class AutoModFilter(db.Model):
    """Фильтры автомодерации"""
    id = db.Column(db.Integer, primary_key=True)
    subreddit_id = db.Column(db.Integer, db.ForeignKey('subreddit.id'), nullable=False)
    
    filter_type = db.Column(db.String(20), nullable=False)  # keyword, regex
    pattern = db.Column(db.String(200), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # remove, flag, message
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
