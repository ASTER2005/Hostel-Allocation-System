"""Role-based access control decorator."""
from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def role_required(*roles):
    """Restricts view function access to users holding any of the specified roles."""
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return inner
    return wrapper
