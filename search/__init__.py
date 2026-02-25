from flask import Blueprint

bp = Blueprint('search', __name__)

from . import views  # noqa: E402,F401