from flask import Blueprint

bp = Blueprint('posts', __name__)

from . import views  # noqa: E402,F401