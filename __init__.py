from flask import Flask
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .models import User, db  # Import User and db from models
import os  # For environment variables


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')  # Use env variable for security
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///site.db')  # Use env variable
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications to save memory
    
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load config from Config class
    # Initialize extensions
    db.init_app(app)  # Bind SQLAlchemy to app
    migrate = Migrate(app, db)  # Set up migration
    login_manager = LoginManager(app)  # Pass the app instance to LoginManager
    login_manager.login_view = 'main.login'  # Redirect to login view when not authenticated

    # User loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Load user by ID from database

    # Register blueprints
    from .routes import main  # Ensure main routes are imported
    app.register_blueprint(main)  # Register the main blueprint

    # Create all database tables if they do not exist
    with app.app_context():
        try:
            db.create_all()  # Create all database tables
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")

    return app  # Return the created app instance
