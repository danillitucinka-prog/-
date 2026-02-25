from flask import jsonify, request, url_for

from . import bp
from models import Post


@bp.route('/api/posts')
def api_posts():
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