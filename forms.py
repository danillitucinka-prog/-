from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, URL
from models import User

class LoginForm(FlaskForm):
    """Форма логина"""
    username = StringField('Ник пользователя', validators=[
        DataRequired('Введите ник'),
        Length(min=3, max=80, message='Ник должен быть 3-80 символов')
    ])
    password = PasswordField('Пароль', validators=[DataRequired('Введите пароль')])
    remember_me = BooleanField('Помнить меня')
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    """Форма регистрации"""
    username = StringField('Ник пользователя', validators=[
        DataRequired('Введите ник'),
        Length(min=3, max=80, message='Ник должен быть 3-80 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired('Введите email'),
        Email('Некорректный email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired('Введите пароль'),
        Length(min=6, message='Пароль минимум 6 символов')
    ])
    password_confirm = PasswordField('Повторите пароль', validators=[
        DataRequired('Подтвердите пароль'),
        EqualTo('password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Этот ник уже занят')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Этот email уже зарегистрирован')

class ChangePasswordForm(FlaskForm):
    """Форма смены пароля"""
    password_old = PasswordField('Старый пароль', validators=[DataRequired('Введите старый пароль')])
    password_new = PasswordField('Новый пароль', validators=[
        DataRequired('Введите новый пароль'),
        Length(min=6, message='Пароль минимум 6 символов')
    ])
    password_confirm = PasswordField('Повторите новый пароль', validators=[
        DataRequired('Подтвердите пароль'),
        EqualTo('password_new', message='Пароли не совпадают')
    ])
    submit = SubmitField('Изменить пароль')

class EditProfileForm(FlaskForm):
    """Форма редактирования профиля"""
    bio = TextAreaField('Биография', validators=[Length(max=500)])
    avatar_url = StringField('URL аватарки', validators=[Optional(), URL()])
    language = SelectField('Язык', choices=[('ru', 'Русский'), ('en', 'English')])
    dark_mode = BooleanField('Темная тема')
    submit = SubmitField('Сохранить')

class CreatePostForm(FlaskForm):
    """Форма создания поста"""
    title = StringField('Заголовок', validators=[
        DataRequired('Введите заголовок'),
        Length(min=3, max=300, message='Заголовок 3-300 символов')
    ])
    subreddit = SelectField('Сообщество', coerce=int)
    content_type = SelectField('Тип контента', choices=[
        ('text', 'Текст'),
        ('link', 'Ссылка'),
        ('image', 'Картинка')
    ])
    content = TextAreaField('Содержание')
    url = StringField('URL')
    flair = StringField('Флейр', validators=[Length(max=50)])
    tags = StringField('Теги (через запятую)', validators=[Length(max=200)])
    submit = SubmitField('Опубликовать')

class EditPostForm(FlaskForm):
    """Форма редактирования поста"""
    title = StringField('Заголовок', validators=[
        DataRequired('Введите заголовок'),
        Length(min=3, max=300, message='Заголовок 3-300 символов')
    ])
    content = TextAreaField('Содержание')
    flair = StringField('Флейр', validators=[Length(max=50)])
    tags = StringField('Теги (через запятую)', validators=[Length(max=200)])
    submit = SubmitField('Сохранить')

class CreateCommentForm(FlaskForm):
    """Форма создания комментария"""
    content = TextAreaField('Комментарий', validators=[
        DataRequired('Напишите комментарий'),
        Length(min=1, max=5000, message='Комментарий 1-5000 символов')
    ])
    submit = SubmitField('Отправить')

class CreateSubredditForm(FlaskForm):
    """Форма создания сообщества"""
    name = StringField('Название (r/)', validators=[
        DataRequired('Введите название'),
        Length(min=3, max=50, message='Название 3-50 символов')
    ])
    title = StringField('Полное название', validators=[
        DataRequired('Введите название'),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Описание', validators=[Length(max=1000)])
    is_private = BooleanField('Приватное сообщество')
    submit = SubmitField('Создать')

    def validate_name(self, field):
        from models import Subreddit
        if Subreddit.query.filter_by(name=field.data).first():
            raise ValidationError('Это сообщество уже существует')

class EditSubredditForm(FlaskForm):
    """Форма редактирования сообщества"""
    title = StringField('Полное название', validators=[
        DataRequired('Введите название'),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Описание', validators=[Length(max=1000)])
    rules = TextAreaField('Правила')
    submit = SubmitField('Сохранить')

class SendMessageForm(FlaskForm):
    """Форма отправки сообщения"""
    recipient = StringField('Кому', validators=[DataRequired('Укажите получателя')])
    subject = StringField('Тема')
    content = TextAreaField('Сообщение', validators=[
        DataRequired('Напишите сообщение'),
        Length(min=1, max=10000)
    ])
    submit = SubmitField('Отправить')

class ReportForm(FlaskForm):
    """Форма отчета о нарушении"""
    reason = SelectField('Причина', choices=[
        ('spam', 'Спам'),
        ('harassment', 'Оскорбления'),
        ('hate', 'Ненависть'),
        ('misinformation', 'Дезинформация'),
        ('nsfw', 'Взрослый контент'),
        ('other', 'Другое')
    ])
    description = TextAreaField('Описание')
    submit = SubmitField('Отправить отчет')

class SearchForm(FlaskForm):
    """Форма поиска"""
    q = StringField('Поиск', validators=[DataRequired()])
    search_type = SelectField('Искать по', choices=[
        ('posts', 'Постам'),
        ('users', 'Пользователям'),
        ('communities', 'Сообществам')
    ])
    submit = SubmitField('Искать')
