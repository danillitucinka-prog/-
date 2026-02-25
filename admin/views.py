from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from functools import wraps

from . import bp
from models import db, User, Post, Comment, Subreddit, Report


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Только администраторы могут это делать', 'danger')
            return redirect(url_for('posts.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/admin')
@admin_required

def admin_panel():
    user_count = User.query.count()
    post_count = Post.query.count()
    comment_count = Comment.query.count()
    subreddit_count = Subreddit.query.count()

    return render_template('admin/panel.html', 
                          user_count=user_count,
                          post_count=post_count,
                          comment_count=comment_count,
                          subreddit_count=subreddit_count)


@bp.route('/admin/users')
@admin_required

def admin_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)


@bp.route('/admin/user/<int:user_id>/ban', methods=['POST'])
@admin_required

def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Вы не можете заблокировать себя', 'danger')
    else:
        user.is_banned = True
        current_user.add_log('ban_user', f'Banned user {user.username}')
        db.session.commit()
        flash(f'Пользователь {user.username} заблокирован', 'success')
    return redirect(url_for('admin.admin_users'))


@bp.route('/admin/user/<int:user_id>/unban', methods=['POST'])
@admin_required

def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    current_user.add_log('unban_user', f'Unbanned user {user.username}')
    db.session.commit()
    flash(f'Пользователь {user.username} разблокирован', 'success')
    return redirect(url_for('admin.admin_users'))


@bp.route('/admin/reports')
@admin_required

def admin_reports():
    page = request.args.get('page', 1, type=int)
    reports = Report.query.filter_by(status='pending').paginate(page=page, per_page=20)
    return render_template('admin/reports.html', reports=reports)


@bp.route('/admin/report/<int:report_id>/dismiss', methods=['POST'])
@admin_required

def dismiss_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = 'dismissed'
    db.session.commit()
    flash('Отчет отклонен', 'success')
    return redirect(url_for('admin.admin_reports'))