from flask import Blueprint

bp = Blueprint('api', __name__)

from . import views  # noqa: E402,F401