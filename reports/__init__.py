from flask import Blueprint

bp = Blueprint('reports', __name__)

from . import views  # noqa: E402,F401