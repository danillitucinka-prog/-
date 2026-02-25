from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import bp
from models import db, Subreddit, Post
from forms import CreateSubredditForm, EditSubredditForm


@bp.route('/r/<subreddit_name>')
def view_subreddit(subreddit_name):
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


@bp.route('/r/create', methods=['GET', 'POST'])
@login_required

def create_subreddit():
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
        return redirect(url_for('subreddits.view_subreddit', subreddit_name=subreddit.name))

    return render_template('subreddits/create.html', form=form)


@bp.route('/r/<subreddit_name>/join', methods=['POST'])
@login_required

def join_subreddit(subreddit_name):
    subreddit = Subreddit.query.filter_by(name=subreddit_name).first_or_404()
    current_user.join_community(subreddit)
    subreddit.member_count += 1
    current_user.add_log('join_subreddit', f'Joined r/{subreddit.name}')
    db.session.commit()
    flash(f'Вы вступили в r/{subreddit.name}', 'success')
    return redirect(url_for('subreddits.view_subreddit', subreddit_name=subreddit.name))


@bp.route('/r/<subreddit_name>/leave', methods=['POST'])
@login_required

def leave_subreddit(subreddit_name):
    subreddit = Subreddit.query.filter_by(name=subreddit_name).first_or_404()
    current_user.leave_community(subreddit)
    subreddit.member_count -= 1
    current_user.add_log('leave_subreddit', f'Left r/{subreddit.name}')
    db.session.commit()
    flash(f'Вы вышли из r/{subreddit.name}', 'success')
    return redirect(url_for('posts.index'))


@bp.route('/r/<subreddit_name>/edit', methods=['GET', 'POST'])
@login_required

def edit_subreddit(subreddit_name):
    subreddit = Subreddit.query.filter_by(name=subreddit_name).first_or_404()

    if subreddit.moderator_id != current_user.id and current_user.role != 'admin':
        flash('Вы не можете редактировать это сообщество', 'danger')
        return redirect(url_for('subreddits.view_subreddit', subreddit_name=subreddit.name))

    form = EditSubredditForm()
    if form.validate_on_submit():
        subreddit.title = form.title.data
        subreddit.description = form.description.data
        subreddit.rules = form.rules.data
        current_user.add_log('edit_subreddit', f'Edited r/{subreddit.name}')
        db.session.commit()
        flash('Сообщество обновлено', 'success')
        return redirect(url_for('subreddits.view_subreddit', subreddit_name=subreddit.name))
    elif request.method == 'GET':
        form.title.data = subreddit.title
        form.description.data = subreddit.description
        form.rules.data = subreddit.rules

    return render_template('subreddits/edit.html', subreddit=subreddit, form=form)
