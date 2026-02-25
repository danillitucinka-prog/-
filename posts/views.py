from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import bp
from models import db, Post, PostVote, Comment, CommentVote, Award, User
from forms import CreatePostForm, EditPostForm, CreateCommentForm, ReportForm


@bp.route('/')
def index():
    # home page logic moved from app.py
    sort = request.args.get('sort', 'hot')  # hot, new, top
    page = request.args.get('page', 1, type=int)
    subreddit = request.args.get('subreddit')

    posts_query = Post.query.filter_by(is_deleted=False)
    if subreddit:
        posts_query = posts_query.join(Post.subreddit).filter(Subreddit.name == subreddit)

    if sort == 'new':
        posts = posts_query.order_by(Post.created_at.desc())
    elif sort == 'top':
        posts = posts_query.order_by(Post.score.desc())
    else:
        posts = posts_query.order_by(Post.created_at.desc())  # placeholder for hot

    posts = posts.paginate(page=page, per_page=20)
    return render_template('posts/index.html', posts=posts, sort=sort)


@bp.route('/post/create', methods=['GET', 'POST'])
@login_required

def create_post():
    form = CreatePostForm()
    # subreddit choices must be populated in view or form
    form.subreddit.choices = [(s.id, s.name) for s in Subreddit.query.all()]
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            subreddit_id=form.subreddit.data,
            content_type=form.content_type.data,
            content=form.content.data,
            url=form.url.data,
            flair=form.flair.data,
            tags=form.tags.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash('Пост создан', 'success')
        return redirect(url_for('posts.view_post', post_id=post.id))
    return render_template('posts/create.html', form=form)


@bp.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('posts/view.html', post=post)


@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required

def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author_id != current_user.id and current_user.role != 'admin':
        flash('Вы не можете редактировать этот пост', 'danger')
        return redirect(url_for('posts.view_post', post_id=post.id))

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
        return redirect(url_for('posts.view_post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.flair.data = post.flair
        form.tags.data = post.tags

    return render_template('posts/edit.html', post=post, form=form)


@bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required

def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author_id != current_user.id and current_user.role != 'admin':
        flash('Вы не можете удалить этот пост', 'danger')
        return redirect(url_for('posts.view_post', post_id=post.id))

    post.is_deleted = True
    current_user.add_log('delete_post', f'Deleted post: {post.title[:50]}')
    db.session.commit()
    flash('Пост удален', 'success')
    return redirect(url_for('posts.index'))


@bp.route('/post/<int:post_id>/pin', methods=['POST'])
@login_required

def pin_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.subreddit.moderator_id != current_user.id and current_user.role != 'admin':
        flash('Вы не можете закрепить этот пост', 'danger')
        return redirect(url_for('posts.view_post', post_id=post.id))

    post.is_pinned = not post.is_pinned
    current_user.add_log('pin_post', f'{"Pinned" if post.is_pinned else "Unpinned"} post')
    db.session.commit()
    flash('Статус закрепления изменен', 'success')
    return redirect(url_for('posts.view_post', post_id=post.id))


@bp.route('/post/<int:post_id>/save', methods=['POST'])
@login_required

def save_post(post_id):
    post = Post.query.get_or_404(post_id)
    current_user.save_post(post)
    current_user.add_log('save_post', f'Saved post: {post.title[:50]}')
    flash('Пост сохранен в избранное', 'success')
    return redirect(request.referrer or url_for('posts.index'))


@bp.route('/post/<int:post_id>/unsave', methods=['POST'])
@login_required

def unsave_post(post_id):
    post = Post.query.get_or_404(post_id)
    current_user.unsave_post(post)
    current_user.add_log('unsave_post', f'Unsaved post: {post.title[:50]}')
    flash('Пост удален из избранного', 'success')
    return redirect(request.referrer or url_for('posts.index'))


@bp.route('/post/<int:post_id>/share')
def share_post(post_id):
    post = Post.query.get_or_404(post_id)
    post_link = url_for('posts.view_post', post_id=post.id, _external=True)
    return jsonify({'link': post_link})


# VOTE ROUTES
@bp.route('/post/<int:post_id>/upvote', methods=['POST'])
@login_required

def upvote_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_vote = PostVote.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    if existing_vote:
        if existing_vote.vote_type == 'upvote':
            db.session.delete(existing_vote)
            post.upvotes -= 1
        else:
            existing_vote.vote_type = 'upvote'
            post.downvotes -= 1
            post.upvotes += 1
            post.author.karma += 2
    else:
        vote = PostVote(user_id=current_user.id, post_id=post.id, vote_type='upvote')
        db.session.add(vote)
        post.upvotes += 1
        post.author.karma += 1

    current_user.add_log('upvote_post', f'Upvoted post')
    db.session.commit()
    return jsonify({'upvotes': post.upvotes, 'downvotes': post.downvotes})


@bp.route('/post/<int:post_id>/downvote', methods=['POST'])
@login_required

def downvote_post(post_id):
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
@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required

def create_comment(post_id):
    post = Post.query.get_or_404(post_id)
    last_comment = Comment.query.filter_by(author_id=current_user.id).order_by(
        Comment.created_at.desc()).first()
    if last_comment and (datetime.utcnow() - last_comment.created_at).seconds < 10:
        flash('Попробуйте через 10 секунд', 'danger')
        return redirect(url_for('posts.view_post', post_id=post.id))

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

        if post.author_id != current_user.id:
            notification = Notification(
                user_id=post.author_id,
                notification_type='reply',
                title=f'{current_user.username} ответил на ваш пост',
                content=comment.content[:100],
                link=url_for('posts.view_post', post_id=post.id)
            )
            db.session.add(notification)
            db.session.commit()

        flash('Комментарий добавлен', 'success')

    return redirect(url_for('posts.view_post', post_id=post.id))


@bp.route('/comment/<int:comment_id>/upvote', methods=['POST'])
@login_required

def upvote_comment(comment_id):
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


@bp.route('/comment/<int:comment_id>/downvote', methods=['POST'])
@login_required

def downvote_comment(comment_id):
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


@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required

def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.author_id != current_user.id and current_user.role != 'admin':
        flash('Вы не можете удалить этот комментарий', 'danger')
        return redirect(url_for('posts.view_post', post_id=comment.post_id))

    comment.is_deleted = True
    comment.post.comment_count -= 1
    current_user.add_log('delete_comment', f'Deleted comment')
    db.session.commit()
    flash('Комментарий удален', 'success')
    return redirect(url_for('posts.view_post', post_id=comment.post_id))
