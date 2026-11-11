from flask import Blueprint
bp = Blueprint("warden", __name__, url_prefix="/warden")
from . import routes  # noqa: E402,F401
