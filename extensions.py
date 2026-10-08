"""
extensions.py — Single place for Flask extension objects.
Keeping them here avoids circular imports between app.py and blueprints.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# Where to send anonymous users when they hit a @login_required route
login_manager.login_view = "auth.login"
login_manager.login_message = "Please login to continue."
login_manager.login_message_category = "warning"
