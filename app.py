from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import config
from models import db, User, Post, Comment, Subreddit, Message, Notification, Report, UserLog, PostVote, CommentVote, Award
from forms import LoginForm, RegisterForm, ChangePasswordForm, EditProfileForm, CreatePostForm, EditPostForm, CreateCommentForm, CreateSubredditForm, EditSubredditForm, SendMessageForm, ReportForm, SearchForm
from datetime import datetime, timedelta
from functools import wraps
import os
import json

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
    
    # AUTH ROUTES
    @app.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('login'))
        
        return render_template('auth/register.html', form=form)
    
    @app.route('/login', methods=['GET', 'POST'])
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
                    return redirect(url_for('login'))
                
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
    
    @app.route('/logout')
    @login_required
    def logout():
        """Выход пользователя"""
        current_user.is_online = False
        current_user.add_log('logout', 'User logged out')
        db.session.commit()
        logout_user()
        flash('Вы вышли из аккаунта', 'success')
        return redirect(url_for('index'))
    
    @app.route('/support')
    def support():
        """Страница поддержки проекта"""
        return render_template('support.html')
    
    # USER ROUTES
    @app.route('/user/<username>')
    def user_profile(username):
        """Профиль пользователя"""
        user = User.query.filter_by(username=username).first_or_404()
        page = request.args.get('page', 1, type=int)
        posts = user.posts.filter_by(is_deleted=False).order_by(Post.created_at.desc()).paginate(page=page, per_page=20)
        
        return render_template('user/profile.html', user=user, posts=posts)
    
    @app.route('/user/<username>/saved')
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
    
    @app.route('/user/<username>/likes')
    def user_likes(username):
        """Лайки пользователя"""
        user = User.query.filter_by(username=username).first_or_404()
        page = request.args.get('page', 1, type=int)
        
        voted_posts = db.session.query(Post).join(PostVote).filter(
            PostVote.user_id == user.id,
            PostVote.vote_type == 'upvote'
        ).paginate(page=page, per_page=20)
        
        return render_template('user/likes.html', user=user, posts=voted_posts)
    
    @app.route('/settings', methods=['GET', 'POST'])
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
            return redirect(url_for('user_profile', username=current_user.username))
        elif request.method == 'GET':
            form.bio.data = current_user.bio
            form.avatar_url.data = current_user.avatar_url
            form.language.data = current_user.language
            form.dark_mode.data = current_user.dark_mode
        
        return render_template('user/settings.html', form=form)
    
    @app.route('/change-password', methods=['GET', 'POST'])
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
                return redirect(url_for('user_profile', username=current_user.username))
        
        return render_template('user/change_password.html', form=form)
    
    @app.route('/delete-account', methods=['POST'])
    @login_required
    def delete_account():
        """Удаление аккаунта"""
        password = request.form.get('password')
        if not current_user.check_password(password):
            flash('Пароль неверный', 'danger')
            return redirect(url_for('settings'))
        
        username = current_user.username
        current_user.add_log('account_deleted', 'User deleted account')
        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        flash(f'Аккаунт {username} удален', 'success')
        return redirect(url_for('index'))
    
    @app.route('/users')
    def users_list():
        """Список пользователей"""
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'karma')  # karma, created_at, followers
        
        if sort == 'created_at':
            query = User.query.order_by(User.created_at.desc())
        elif sort == 'followers':
            query = User.query.order_by(User.followers.noop().desc())
        else:
            query = User.query.order_by(User.karma.desc())
        
        users = query.paginate(page=page, per_page=20)
        return render_template('users/list.html', users=users, sort=sort)
    
    @app.route('/user/<username>/follow', methods=['POST'])
    @login_required
    def follow_user(username):
        """Подписаться на пользователя"""
        user = User.query.filter_by(username=username).first_or_404()
        if user == current_user:
            flash('Вы не можете подписаться на себя', 'danger')
        else:
            current_user.follow(user)
            current_user.add_log('follow_user', f'Followed {username}')
            
            # Уведомление
            notification = Notification(
                user_id=user.id,
                notification_type='follow',
                title=f'{current_user.username} подписался на вас',
                link=url_for('user_profile', username=current_user.username)
            )
            db.session.add(notification)
            db.session.commit()
            flash(f'Вы подписались на {username}', 'success')
        
        return redirect(url_for('user_profile', username=username))
    
    @app.route('/user/<username>/unfollow', methods=['POST'])
    @login_required
    def unfollow_user(username):
        """Отписаться от пользователя"""
        user = User.query.filter_by(username=username).first_or_404()
        current_user.unfollow(user)
        current_user.add_log('unfollow_user', f'Unfollowed {username}')
        db.session.commit()
        flash(f'Вы отписались от {username}', 'success')
        return redirect(url_for('user_profile', username=username))
    
    @app.route('/user/<username>/block', methods=['POST'])
    @login_required
    def block_user(username):
        """Заблокировать пользователя"""
        user = User.query.filter_by(username=username).first_or_404()
        current_user.block_user(user)
        current_user.add_log('block_user', f'Blocked {username}')
        db.session.commit()
        flash(f'Вы заблокировали {username}', 'success')
        return redirect(url_for('user_profile', username=username))
    
    @app.route('/user/<username>/unblock', methods=['POST'])
    @login_required
    def unblock_user(username):
        """Разблокировать пользователя"""
        user = User.query.filter_by(username=username).first_or_404()
        current_user.unblock_user(user)
        current_user.add_log('unblock_user', f'Unblocked {username}')
        db.session.commit()
        flash(f'Вы разблокировали {username}', 'success')
        return redirect(url_for('user_profile', username=username))
    
    # POST ROUTES
    @app.route('/')
    def index():
        """Главная страница"""
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'hot')  # hot, new, top
        
        # Фильтр по заблокированным пользователям
        blocked_users = current_user.blocking if current_user.is_authenticated else []
        blocked_ids = [u.id for u in blocked_users]
        
        query = Post.query.filter(Post.is_deleted == False)
        if blocked_ids:
            query = query.filter(~Post.author_id.in_(blocked_ids))
        
        if sort == 'new':
            query = query.order_by(Post.created_at.desc())
        elif sort == 'top':
            query = query.filter(Post.created_at >= datetime.utcnow() - timedelta(weeks=1))
            query = query.order_by(Post.upvotes.desc())
        else:  # hot
            query = query.order_by((Post.upvotes - Post.downvotes).desc())
        
        posts = query.paginate(page=page, per_page=20)
        return render_template('posts/index.html', posts=posts, sort=sort)
    
    @app.route('/post/create', methods=['GET', 'POST'])
    @login_required
    def create_post():
        """Создание поста"""
        form = CreatePostForm()
        form.subreddit.choices = [(s.id, f'r/{s.name}') for s in current_user.communities]
        
        if not form.subreddit.choices:
            flash('Вступите в сообщество, чтобы создать пост', 'info')
            return redirect(url_for('index'))
        
        if form.validate_on_submit():
            # Проверка спама
            last_post = Post.query.filter_by(author_id=current_user.id).order_by(
                Post.created_at.desc()).first()
            if last_post and (datetime.utcnow() - last_post.created_at).seconds < 60:
                flash('Попробуйте через минуту', 'danger')
                return redirect(url_for('index'))
            
            post = Post(
                title=form.title.data,
                content=form.content.data,
                content_type=form.content_type.data,
                url=form.url.data,
                flair=form.flair.data,
                tags=form.tags.data,
                author_id=current_user.id,
                subreddit_id=form.subreddit.data
            )
            current_user.add_log('create_post', f'Created post: {post.title[:50]}')
            db.session.add(post)
            db.session.commit()
            
            flash('Пост опубликован!', 'success')
            return redirect(url_for('view_post', post_id=post.id))
        
        return render_template('posts/create.html', form=form)
    
    @app.route('/post/<int:post_id>')
    def view_post(post_id):
        """Просмотр поста"""
        post = Post.query.get_or_404(post_id)
        
        if post.is_deleted:
            flash('Этот пост удален', 'danger')
            return redirect(url_for('index'))
        
        # Увеличить счетчик просмотров
        post.increment_views()
        
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'best')  # best, new, old, top, bottom
        
        query = Comment.query.filter_by(post_id=post.id, is_deleted=False, parent_comment_id=None)
        
        if sort == 'new':
            query = query.order_by(Comment.created_at.desc())
        elif sort == 'old':
            query = query.order_by(Comment.created_at.asc())
        elif sort == 'top':
            query = query.order_by((Comment.upvotes - Comment.downvotes).desc())
        elif sort == 'bottom':
            query = query.order_by((Comment.upvotes - Comment.downvotes).asc())
        else:  # best
            query = query.order_by((Comment.upvotes - Comment.downvotes).desc())
        
        comments = query.paginate(page=page, per_page=10)
        form = CreateCommentForm()
        
        return render_template('posts/view.html', post=post, comments=comments, form=form, sort=sort)
    
    @app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_post(post_id):
        """Редактирование поста"""
        post = Post.query.get_or_404(post_id)
        
        if post.author_id != current_user.id and current_user.role != 'admin':
            flash('Вы не можете редактировать этот пост', 'danger')
            return redirect(url_for('view_post', post_id=post.id))
        
        form = EditPostForm()
        if form.validate_on_submit():
            post.title = form.title.data
            post.content = form.content.data
            post.flair = form.flair.data
            post.tags = form.tags.data
            post.updated_at = datetime.utcnow()
            current_user.add_log('edit_post', f'Edited post: {post.title[:50]}')
            db.session.commit()
            flash('Пост обновлен', 'success')
            return redirect(url_for('view_post', post_id=post.id))
        elif request.method == 'GET':
            form.title.data = post.title
            form.content.data = post.content
            form.flair.data = post.flair
            form.tags.data = post.tags
        
        return render_template('posts/edit.html', post=post, form=form)
    
    @app.route('/post/<int:post_id>/delete', methods=['POST'])
    @login_required
    def delete_post(post_id):
        """Удаление поста"""
        post = Post.query.get_or_404(post_id)
        
        if post.author_id != current_user.id and current_user.role != 'admin':
            flash('Вы не можете удалить этот пост', 'danger')
            return redirect(url_for('view_post', post_id=post.id))
        
        post.is_deleted = True
        current_user.add_log('delete_post', f'Deleted post: {post.title[:50]}')
        db.session.commit()
        flash('Пост удален', 'success')
        return redirect(url_for('index'))
    
    @app.route('/post/<int:post_id>/pin', methods=['POST'])
    @login_required
    def pin_post(post_id):
        """Закрепление поста"""
        post = Post.query.get_or_404(post_id)
        
        if post.subreddit.moderator_id != current_user.id and current_user.role != 'admin':
            flash('Вы не можете закрепить этот пост', 'danger')
            return redirect(url_for('view_post', post_id=post.id))
        
        post.is_pinned = not post.is_pinned
        current_user.add_log('pin_post', f'{"Pinned" if post.is_pinned else "Unpinned"} post')
        db.session.commit()
        flash('Статус закрепления изменен', 'success')
        return redirect(url_for('view_post', post_id=post.id))
    
    @app.route('/post/<int:post_id>/save', methods=['POST'])
    @login_required
    def save_post(post_id):
        """Сохранение поста"""
        post = Post.query.get_or_404(post_id)
        current_user.save_post(post)
        current_user.add_log('save_post', f'Saved post: {post.title[:50]}')
        flash('Пост сохранен в избранное', 'success')
        return redirect(request.referrer or url_for('index'))
    
    @app.route('/post/<int:post_id>/unsave', methods=['POST'])
    @login_required
    def unsave_post(post_id):
        """Удаление поста из избранного"""
        post = Post.query.get_or_404(post_id)
        current_user.unsave_post(post)
        current_user.add_log('unsave_post', f'Unsaved post: {post.title[:50]}')
        flash('Пост удален из избранного', 'success')
        return redirect(request.referrer or url_for('index'))
    
    @app.route('/post/<int:post_id>/share')
    def share_post(post_id):
        """Получение ссылки на пост"""
        post = Post.query.get_or_404(post_id)
        post_link = url_for('view_post', post_id=post.id, _external=True)
        return jsonify({'link': post_link})
    
    # VOTE ROUTES
    @app.route('/post/<int:post_id>/upvote', methods=['POST'])
    @login_required
    def upvote_post(post_id):
        """Лайк поста"""
        post = Post.query.get_or_404(post_id)
        
        # Проверить существующий голос
        existing_vote = PostVote.query.filter_by(user_id=current_user.id, post_id=post.id).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'upvote':
                # Отменить лайк
                db.session.delete(existing_vote)
                post.upvotes -= 1
            else:
                # Изменить с дизлайка на лайк
                existing_vote.vote_type = 'upvote'
                post.downvotes -= 1
                post.upvotes += 1
                post.author.karma += 2  # +2 за отмену дизлайка и добавление лайка
        else:
            # Добавить новый лайк
            vote = PostVote(user_id=current_user.id, post_id=post.id, vote_type='upvote')
            db.session.add(vote)
            post.upvotes += 1
            post.author.karma += 1
        
        current_user.add_log('upvote_post', f'Upvoted post')
        db.session.commit()
        return jsonify({'upvotes': post.upvotes, 'downvotes': post.downvotes})
    
    @app.route('/post/<int:post_id>/downvote', methods=['POST'])
    @login_required
    def downvote_post(post_id):
        """Дизлайк поста"""
        post = Post.query.get_or_404(post_id)
        
        existing_vote = PostVote.query.filter_by(user_id=current_user.id, post_id=post.id).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'downvote':
                db.session.delete(existing_vote)
                post.downvotes -= 1
            else:
                existing_vote.vote_type = 'downvote'
                post.upvotes -= 1
                post.downvotes += 1
                post.author.karma -= 2
        else:
            vote = PostVote(user_id=current_user.id, post_id=post.id, vote_type='downvote')
            db.session.add(vote)
            post.downvotes += 1
            post.author.karma -= 1
        
        current_user.add_log('downvote_post', f'Downvoted post')
        db.session.commit()
        return jsonify({'upvotes': post.upvotes, 'downvotes': post.downvotes})
    
    # COMMENT ROUTES
    @app.route('/post/<int:post_id>/comment', methods=['POST'])
    @login_required
    def create_comment(post_id):
        """Создание комментария"""
        post = Post.query.get_or_404(post_id)
        
        # Проверка спама
        last_comment = Comment.query.filter_by(author_id=current_user.id).order_by(
            Comment.created_at.desc()).first()
        if last_comment and (datetime.utcnow() - last_comment.created_at).seconds < 10:
            flash('Попробуйте через 10 секунд', 'danger')
            return redirect(url_for('view_post', post_id=post.id))
        
        form = CreateCommentForm()
        if form.validate_on_submit():
            comment = Comment(
                content=form.content.data,
                author_id=current_user.id,
                post_id=post.id
            )
            post.comment_count += 1
            current_user.add_log('create_comment', f'Created comment on post {post.id}')
            db.session.add(comment)
            db.session.commit()
            
            # Уведомление автору поста
            if post.author_id != current_user.id:
                notification = Notification(
                    user_id=post.author_id,
                    notification_type='reply',
                    title=f'{current_user.username} ответил на ваш пост',
                    content=comment.content[:100],
                    link=url_for('view_post', post_id=post.id)
                )
                db.session.add(notification)
                db.session.commit()
            
            flash('Комментарий добавлен', 'success')
        
        return redirect(url_for('view_post', post_id=post.id))
    
    @app.route('/comment/<int:comment_id>/upvote', methods=['POST'])
    @login_required
    def upvote_comment(comment_id):
        """Лайк комментария"""
        comment = Comment.query.get_or_404(comment_id)
        
        existing_vote = CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment.id).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'upvote':
                db.session.delete(existing_vote)
                comment.upvotes -= 1
            else:
                existing_vote.vote_type = 'upvote'
                comment.downvotes -= 1
                comment.upvotes += 1
                comment.author.karma += 2
        else:
            vote = CommentVote(user_id=current_user.id, comment_id=comment.id, vote_type='upvote')
            db.session.add(vote)
            comment.upvotes += 1
            comment.author.karma += 1
        
        db.session.commit()
        return jsonify({'upvotes': comment.upvotes, 'downvotes': comment.downvotes})
    
    @app.route('/comment/<int:comment_id>/downvote', methods=['POST'])
    @login_required
    def downvote_comment(comment_id):
        """Дизлайк комментария"""
        comment = Comment.query.get_or_404(comment_id)
        
        existing_vote = CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment.id).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'downvote':
                db.session.delete(existing_vote)
                comment.downvotes -= 1
            else:
                existing_vote.vote_type = 'downvote'
                comment.upvotes -= 1
                comment.downvotes += 1
                comment.author.karma -= 2
        else:
            vote = CommentVote(user_id=current_user.id, comment_id=comment.id, vote_type='downvote')
            db.session.add(vote)
            comment.downvotes += 1
            comment.author.karma -= 1
        
        db.session.commit()
        return jsonify({'upvotes': comment.upvotes, 'downvotes': comment.downvotes})
    
    @app.route('/comment/<int:comment_id>/delete', methods=['POST'])
    @login_required
    def delete_comment(comment_id):
        """Удаление комментария"""
        comment = Comment.query.get_or_404(comment_id)
        
        if comment.author_id != current_user.id and current_user.role != 'admin':
            flash('Вы не можете удалить этот комментарий', 'danger')
            return redirect(url_for('view_post', post_id=comment.post_id))
        
        comment.is_deleted = True
        comment.post.comment_count -= 1
        current_user.add_log('delete_comment', f'Deleted comment')
        db.session.commit()
        flash('Комментарий удален', 'success')
        return redirect(url_for('view_post', post_id=comment.post_id))
    
    # SUBREDDIT ROUTES
    @app.route('/r/<subreddit_name>')
    def view_subreddit(subreddit_name):
        """Просмотр сообщества"""
        subreddit = Subreddit.query.filter_by(name=subreddit_name).first_or_404()
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'hot')
        
        query = Post.query.filter_by(subreddit_id=subreddit.id, is_deleted=False)
        
        if sort == 'new':
            query = query.order_by(Post.created_at.desc())
        elif sort == 'top':
            query = query.order_by(Post.upvotes.desc())
        else:
            query = query.order_by((Post.upvotes - Post.downvotes).desc())
        
        posts = query.paginate(page=page, per_page=20)
        return render_template('subreddits/view.html', subreddit=subreddit, posts=posts, sort=sort)
    
    @app.route('/r/create', methods=['GET', 'POST'])
    @login_required
    def create_subreddit():
        """Создание сообщества"""
        form = CreateSubredditForm()
        if form.validate_on_submit():
            subreddit = Subreddit(
                name=form.name.data,
                title=form.title.data,
                description=form.description.data,
                is_private=form.is_private.data,
                moderator_id=current_user.id
            )
            current_user.join_community(subreddit)
            current_user.add_log('create_subreddit', f'Created subreddit r/{subreddit.name}')
            db.session.add(subreddit)
            db.session.commit()
            flash('Сообщество создано!', 'success')
            return redirect(url_for('view_subreddit', subreddit_name=subreddit.name))
        
        return render_template('subreddits/create.html', form=form)
    
    @app.route('/r/<subreddit_name>/join', methods=['POST'])
    @login_required
    def join_subreddit(subreddit_name):
        """Вступление в сообщество"""
        subreddit = Subreddit.query.filter_by(name=subreddit_name).first_or_404()
        current_user.join_community(subreddit)
        subreddit.member_count += 1
        current_user.add_log('join_subreddit', f'Joined r/{subreddit.name}')
        db.session.commit()
        flash(f'Вы вступили в r/{subreddit.name}', 'success')
        return redirect(url_for('view_subreddit', subreddit_name=subreddit.name))
    
    @app.route('/r/<subreddit_name>/leave', methods=['POST'])
    @login_required
    def leave_subreddit(subreddit_name):
        """Выход из сообщества"""
        subreddit = Subreddit.query.filter_by(name=subreddit_name).first_or_404()
        current_user.leave_community(subreddit)
        subreddit.member_count -= 1
        current_user.add_log('leave_subreddit', f'Left r/{subreddit.name}')
        db.session.commit()
        flash(f'Вы вышли из r/{subreddit.name}', 'success')
        return redirect(url_for('index'))
    
    @app.route('/r/<subreddit_name>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_subreddit(subreddit_name):
        """Редактирование сообщества"""
        subreddit = Subreddit.query.filter_by(name=subreddit_name).first_or_404()
        
        if subreddit.moderator_id != current_user.id and current_user.role != 'admin':
            flash('Вы не можете редактировать это сообщество', 'danger')
            return redirect(url_for('view_subreddit', subreddit_name=subreddit.name))
        
        form = EditSubredditForm()
        if form.validate_on_submit():
            subreddit.title = form.title.data
            subreddit.description = form.description.data
            subreddit.rules = form.rules.data
            current_user.add_log('edit_subreddit', f'Edited r/{subreddit.name}')
            db.session.commit()
            flash('Сообщество обновлено', 'success')
            return redirect(url_for('view_subreddit', subreddit_name=subreddit.name))
        elif request.method == 'GET':
            form.title.data = subreddit.title
            form.description.data = subreddit.description
            form.rules.data = subreddit.rules
        
        return render_template('subreddits/edit.html', subreddit=subreddit, form=form)
    
    # MESSAGES ROUTES
    @app.route('/messages')
    @login_required
    def messages():
        """Входящие сообщения"""
        page = request.args.get('page', 1, type=int)
        messages = Message.query.filter_by(recipient_id=current_user.id).order_by(
            Message.created_at.desc()).paginate(page=page, per_page=20)
        return render_template('messages/inbox.html', messages=messages)
    
    @app.route('/messages/<int:message_id>')
    @login_required
    def view_message(message_id):
        """Просмотр сообщения"""
        message = Message.query.get_or_404(message_id)
        
        if message.recipient_id != current_user.id:
            flash('Вы не можете просматривать это сообщение', 'danger')
            return redirect(url_for('messages'))
        
        message.is_read = True
        db.session.commit()
        return render_template('messages/view.html', message=message)
    
    @app.route('/messages/send/<username>', methods=['GET', 'POST'])
    @login_required
    def send_message(username):
        """Отправка сообщения"""
        recipient = User.query.filter_by(username=username).first_or_404()
        
        if recipient == current_user:
            flash('Вы не можете написать себе', 'danger')
            return redirect(url_for('user_profile', username=username))
        
        form = SendMessageForm()
        form.recipient.data = recipient.username
        form.recipient.render_kw = {'readonly': True}
        
        if form.validate_on_submit():
            message = Message(
                sender_id=current_user.id,
                recipient_id=recipient.id,
                subject=form.subject.data,
                content=form.content.data
            )
            current_user.add_log('send_message', f'Sent message to {recipient.username}')
            db.session.add(message)
            db.session.commit()
            
            # Уведомление
            notification = Notification(
                user_id=recipient.id,
                notification_type='message',
                title=f'Новое сообщение от {current_user.username}',
                content=form.subject.data,
                link=url_for('view_message', message_id=message.id)
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Сообщение отправлено', 'success')
            return redirect(url_for('messages'))
        
        return render_template('messages/send.html', form=form, recipient=recipient)
    
    # SEARCH ROUTES
    @app.route('/search', methods=['GET', 'POST'])
    def search():
        """Поиск"""
        form = SearchForm()
        results = None
        
        if form.validate_on_submit():
            q = form.q.data
            search_type = form.search_type.data
            
            if search_type == 'posts':
                results = Post.query.filter(
                    (Post.title.ilike(f'%{q}%') | Post.content.ilike(f'%{q}%')),
                    Post.is_deleted == False
                ).all()
            elif search_type == 'users':
                results = User.query.filter(
                    User.username.ilike(f'%{q}%')
                ).all()
            elif search_type == 'communities':
                results = Subreddit.query.filter(
                    Subreddit.name.ilike(f'%{q}%') | Subreddit.title.ilike(f'%{q}%')
                ).all()
        
        return render_template('search.html', form=form, results=results)
    
    # REPORT ROUTES
    @app.route('/post/<int:post_id>/report', methods=['GET', 'POST'])
    @login_required
    def report_post(post_id):
        """Отчет о нарушении"""
        post = Post.query.get_or_404(post_id)
        form = ReportForm()
        
        if form.validate_on_submit():
            report = Report(
                reporter_id=current_user.id,
                post_id=post.id,
                reason=form.reason.data,
                description=form.description.data
            )
            db.session.add(report)
            db.session.commit()
            flash('Отчет отправлен модераторам', 'success')
            return redirect(url_for('view_post', post_id=post.id))
        
        return render_template('report.html', form=form, post=post)
    
    # ADMIN ROUTES
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != 'admin':
                flash('Только администраторы могут это делать', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/admin')
    @admin_required
    def admin_panel():
        """Панель администратора"""
        user_count = User.query.count()
        post_count = Post.query.count()
        comment_count = Comment.query.count()
        subreddit_count = Subreddit.query.count()
        
        return render_template('admin/panel.html', 
                              user_count=user_count,
                              post_count=post_count,
                              comment_count=comment_count,
                              subreddit_count=subreddit_count)
    
    @app.route('/admin/users')
    @admin_required
    def admin_users():
        """Управление пользователями"""
        page = request.args.get('page', 1, type=int)
        users = User.query.paginate(page=page, per_page=20)
        return render_template('admin/users.html', users=users)
    
    @app.route('/admin/user/<int:user_id>/ban', methods=['POST'])
    @admin_required
    def ban_user(user_id):
        """Блокировка пользователя"""
        user = User.query.get_or_404(user_id)
        if user == current_user:
            flash('Вы не можете заблокировать себя', 'danger')
        else:
            user.is_banned = True
            current_user.add_log('ban_user', f'Banned user {user.username}')
            db.session.commit()
            flash(f'Пользователь {user.username} заблокирован', 'success')
        
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/user/<int:user_id>/unban', methods=['POST'])
    @admin_required
    def unban_user(user_id):
        """Разблокировка пользователя"""
        user = User.query.get_or_404(user_id)
        user.is_banned = False
        current_user.add_log('unban_user', f'Unbanned user {user.username}')
        db.session.commit()
        flash(f'Пользователь {user.username} разблокирован', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/reports')
    @admin_required
    def admin_reports():
        """Просмотр отчетов"""
        page = request.args.get('page', 1, type=int)
        reports = Report.query.filter_by(status='pending').paginate(page=page, per_page=20)
        return render_template('admin/reports.html', reports=reports)
    
    @app.route('/admin/report/<int:report_id>/dismiss', methods=['POST'])
    @admin_required
    def dismiss_report(report_id):
        """Отклонить отчет"""
        report = Report.query.get_or_404(report_id)
        report.status = 'dismissed'
        db.session.commit()
        flash('Отчет отклонен', 'success')
        return redirect(url_for('admin_reports'))
    
    @app.route('/api/posts')
    def api_posts():
        """API эндпоинт для постов"""
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'hot')
        
        query = Post.query.filter_by(is_deleted=False)
        
        if sort == 'new':
            query = query.order_by(Post.created_at.desc())
        elif sort == 'top':
            query = query.order_by(Post.upvotes.desc())
        else:
            query = query.order_by((Post.upvotes - Post.downvotes).desc())
        
        posts = query.paginate(page=page, per_page=20)
        
        return jsonify({
            'posts': [{
                'id': p.id,
                'title': p.title,
                'author': p.author.username,
                'subreddit': p.subreddit.name,
                'upvotes': p.upvotes,
                'downvotes': p.downvotes,
                'comments': p.comment_count,
                'created_at': p.created_at.isoformat()
            } for p in posts.items],
            'total': posts.total,
            'pages': posts.pages
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
