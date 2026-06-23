"""
Flask application factory and configuration.
"""

from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from findmydos.config import get_config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app instances.

    Args:
        config_name: Name of the configuration to use (optional)

    Returns:
        Flask: Configured Flask application instance
    """
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    app = Flask(__name__, instance_relative_config=False, template_folder=template_dir)

    # Make `now()` available inside Jinja templates
    app.jinja_env.globals["now"] = datetime.now

    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(get_config(config_name))

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from findmydos.web.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Create database tables if they don't exist
    with app.app_context():
        from findmydos.storage.database import init_db
        init_db()

    return app
