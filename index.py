"""Vercel WSGI entry point for the Flask application."""

# Use the repository launcher so the established package layout and factory
# remain the single source of app construction.
from run import app

__all__ = ["app"]
