#!/usr/bin/env python3
"""
Production Runner for Whop Gamify App
This script handles production deployment with proper error handling and logging
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Set up production logging."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # File handler
    file_handler = RotatingFileHandler(
        'logs/whop_gamify.log',
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'SECRET_KEY',
        'WHOP_CLIENT_ID',
        'WHOP_CLIENT_SECRET',
        'WHOP_REDIRECT_URI',
        'WHOP_WEBHOOK_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables before running the app.")
        return False
    
    return True

def check_database():
    """Check database connection."""
    try:
        from app import db, User
        # Try to query the database
        User.query.first()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main production runner."""
    print("🚀 Starting Whop Gamify App in Production Mode")
    print("=" * 50)
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Whop Gamify App")
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed")
        sys.exit(1)
    
    # Check database
    if not check_database():
        logger.error("Database check failed")
        sys.exit(1)
    
    try:
        from app import app, init_db
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Get configuration
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Run the app
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False  # Disable reloader in production
        )
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        print("\n👋 Shutting down Whop Gamify App")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
