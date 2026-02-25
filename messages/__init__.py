from flask import Blueprint

bp = Blueprint('messages', __name__)

from . import views  # noqa: E402,F401