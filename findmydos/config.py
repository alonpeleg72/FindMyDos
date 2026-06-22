"""
Configuration management for FindMyDos.
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///findmydos.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Application settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Scraping settings
    SCRAPING_INTERVAL_HOURS = int(os.environ.get('SCRAPING_INTERVAL_HOURS', '2'))
    USER_AGENT = os.environ.get(
        'USER_AGENT',
        'FindMyDos/1.0 (+https://github.com/alonp/findmydos)'
    )
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '30'))

    # NLP settings
    HEBREW_MODEL_NAME = os.environ.get('HEBREW_MODEL_NAME', 'stanfordnlp/stanza_hebrew')

    # Geocoding settings
    GEOCODER_USER_AGENT = os.environ.get('GEOCODER_USER_AGENT', 'findmydos/1.0')
    GEOCODER_TIMEOUT = int(os.environ.get('GEOCODER_TIMEOUT', '10'))

    # Road impact settings
    MAJOR_ROAD_BUFFER_KM = float(os.environ.get('MAJOR_ROAD_BUFFER_KM', '0.5'))

    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """
    Get configuration class by name.

    Args:
        config_name: Name of the configuration to get

    Returns:
        Config: Configuration class
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    return config.get(config_name, config['default'])