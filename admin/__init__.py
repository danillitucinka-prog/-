from flask import Blueprint

bp = Blueprint('admin', __name__)

from . import views  # noqa: E402,F401