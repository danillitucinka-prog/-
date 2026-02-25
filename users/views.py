from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user

from . import bp
from models import db, User, Post, PostVote
from forms import EditProfileForm, ChangePasswordForm


@bp.route('/user/<username>')
def user_profile(username):
    """Профиль пользователя"""
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.filter_by(is_deleted=False).order_by(Post.created_at.desc()).paginate(page=page, per_page=20)

    return render_template('user/profile.html', user=user, posts=posts)


@bp.route('/user/<username>/saved')
@login_required

def user_saved_posts(username):
    """Сохраненные посты"""
    user = User.query.filter_by(username=username).first_or_404()
    if user.id != current_user.id:
        flash('Вы не можете просматривать этот материал', 'danger')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = user.saved.paginate(page=page, per_page=20)
    return render_template('user/saved.html', user=user, posts=posts)


@bp.route('/user/<username>/likes')
def user_likes(username):
    """Лайки пользователя"""
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)

    voted_posts = db.session.query(Post).join(PostVote).filter(
        PostVote.user_id == user.id,
        PostVote.vote_type == 'upvote'
    ).paginate(page=page, per_page=20)

    return render_template('user/likes.html', user=user, posts=voted_posts)


@bp.route('/settings', methods=['GET', 'POST'])
@login_required

def settings():
    """Настройки профиля"""
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.bio = form.bio.data
        current_user.avatar_url = form.avatar_url.data or current_user.avatar_url
        current_user.language = form.language.data
        current_user.dark_mode = form.dark_mode.data
        current_user.add_log('profile_update', 'User updated profile')
        db.session.commit()
        flash('Профиль обновлен', 'success')
        return redirect(url_for('users.user_profile', username=current_user.username))
    elif request.method == 'GET':
        form.bio.data = current_user.bio
        form.avatar_url.data = current_user.avatar_url
        form.language.data = current_user.language
        form.dark_mode.data = current_user.dark_mode

    return render_template('user/settings.html', form=form)


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required

def change_password():
    """Смена пароля"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password_old.data):
            flash('Старый пароль неверный', 'danger')
        else:
            current_user.set_password(form.password_new.data)
            current_user.add_log('password_change', 'User changed password')
            db.session.commit()
            flash('Пароль изменен успешно', 'success')
            return redirect(url_for('users.user_profile', username=current_user.username))

    return render_template('user/change_password.html', form=form)


@bp.route('/delete-account', methods=['POST'])
@login_required

def delete_account():
    """Удаление аккаунта"""
    password = request.form.get('password')
    if not current_user.check_password(password):
        flash('Пароль неверный', 'danger')
        return redirect(url_for('users.settings'))

    username = current_user.username
    current_user.add_log('account_deleted', 'User deleted account')
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash(f'Аккаунт {username} удален', 'success')
    return redirect(url_for('index'))


@bp.route('/users')
def users_list():
    """Список пользователей"""
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'karma')  # karma, created_at, followers

    if sort == 'created_at':
        users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    elif sort == 'followers':
        users = User.query.order_by(User.followers_count.desc()).paginate(page=page, per_page=20)
    else:
        users = User.query.order_by(User.karma.desc()).paginate(page=page, per_page=20)

    return render_template('users/list.html', users=users, sort=sort)


@bp.route('/user/<username>/follow', methods=['POST'])
@login_required

def follow_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash('Нельзя подписаться на себя', 'danger')
        return redirect(url_for('users.user_profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('Вы подписаны', 'success')
    return redirect(url_for('users.user_profile', username=username))


@bp.route('/user/<username>/unfollow', methods=['POST'])
@login_required

def unfollow_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    current_user.unfollow(user)
    db.session.commit()
    flash('Вы отписались', 'success')
    return redirect(url_for('users.user_profile', username=username))


@bp.route('/user/<username>/block', methods=['POST'])
@login_required

def block_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    current_user.block(user)
    db.session.commit()
    flash('Пользователь заблокирован', 'success')
    return redirect(url_for('users.user_profile', username=username))


@bp.route('/user/<username>/unblock', methods=['POST'])
@login_required

def unblock_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    current_user.unblock(user)
    db.session.commit()
    flash('Пользователь разблокирован', 'success')
    return redirect(url_for('users.user_profile', username=username))