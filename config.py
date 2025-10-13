"""
Production Configuration for Whop Gamify App
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///whop_gamify.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Whop Integration
    WHOP_CLIENT_ID = os.environ.get('WHOP_CLIENT_ID')
    WHOP_CLIENT_SECRET = os.environ.get('WHOP_CLIENT_SECRET')
    WHOP_REDIRECT_URI = os.environ.get('WHOP_REDIRECT_URI')
    WHOP_WEBHOOK_SECRET = os.environ.get('WHOP_WEBHOOK_SECRET')
    
    # XP System Configuration
    XP_PER_ACTION = int(os.environ.get('XP_PER_ACTION', '5'))
    XP_PER_DAILY_QUEST = int(os.environ.get('XP_PER_DAILY_QUEST', '25'))
    XP_PER_WEEKLY_QUEST = int(os.environ.get('XP_PER_WEEKLY_QUEST', '100'))
    POINTS_PER_DAILY_QUEST = int(os.environ.get('POINTS_PER_DAILY_QUEST', '1'))
    POINTS_PER_WEEKLY_QUEST = int(os.environ.get('POINTS_PER_WEEKLY_QUEST', '5'))
    
    # Premium Features
    PREMIUM_XP_MULTIPLIER = float(os.environ.get('PREMIUM_XP_MULTIPLIER', '2.0'))
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///whop_gamify_dev.db'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
