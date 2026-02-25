from flask import render_template, request

from . import bp
from models import Post, User, Subreddit
from forms import SearchForm


@bp.route('/search', methods=['GET', 'POST'])
def search():
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