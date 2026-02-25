from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from . import bp
from models import db, User
from forms import LoginForm, RegisterForm


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            avatar_url=f'https://www.gravatar.com/avatar/{form.email.data}?d=identicon'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        user.add_log('registration', 'User registered')
        db.session.commit()

        flash('Регистрация успешна! Пожалуйста, войдите', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Логин пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if user.is_banned:
                flash('Ваш аккаунт заблокирован', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user, remember=form.remember_me.data)
            user.is_online = True
            user.last_login = datetime.utcnow()
            user.add_log('login', 'User logged in')
            db.session.commit()

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверный ник или пароль', 'danger')

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required

def logout():
    """Выход пользователя"""
    current_user.is_online = False
    current_user.add_log('logout', 'User logged out')
    db.session.commit()
    logout_user()
    flash('Вы вышли из аккаунта', 'success')
    return redirect(url_for('index'))


@bp.route('/support')
def support():
    """Страница поддержки проекта"""
    return render_template('support.html')