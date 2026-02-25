from flask import Blueprint

bp = Blueprint('subreddits', __name__)

from . import views  # noqa: E402,F401