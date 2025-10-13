"""
Whop Integration Module
Handles OAuth authentication and API interactions with Whop
"""

import requests
import hmac
import hashlib
from flask import current_app, session, redirect, url_for, request
from functools import wraps
import os

class WhopIntegration:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        app.whop = self
    
    def get_whop_config(self):
        """Get Whop configuration from environment variables."""
        return {
            'client_id': os.environ.get('WHOP_CLIENT_ID'),
            'client_secret': os.environ.get('WHOP_CLIENT_SECRET'),
            'redirect_uri': os.environ.get('WHOP_REDIRECT_URI'),
            'webhook_secret': os.environ.get('WHOP_WEBHOOK_SECRET'),
            'api_base_url': 'https://api.whop.com/v1'
        }
    
    def get_auth_url(self, state=None):
        """Generate Whop OAuth authorization URL."""
        config = self.get_whop_config()
        if not config['client_id'] or not config['redirect_uri']:
            raise ValueError("Whop client_id and redirect_uri must be configured")
        
        params = {
            'client_id': config['client_id'],
            'redirect_uri': config['redirect_uri'],
            'response_type': 'code',
            'scope': 'user:read user:write',
            'state': state or 'default_state'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"https://whop.com/oauth/authorize?{query_string}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token."""
        config = self.get_whop_config()
        
        data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': config['redirect_uri']
        }
        
        response = requests.post('https://whop.com/oauth/token', data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Token exchange failed: {response.text}")
    
    def get_user_info(self, access_token):
        """Get user information from Whop API."""
        config = self.get_whop_config()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{config['api_base_url']}/user", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user info: {response.text}")
    
    def get_user_subscriptions(self, access_token, user_id):
        """Get user's subscription information."""
        config = self.get_whop_config()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{config['api_base_url']}/users/{user_id}/subscriptions",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'subscriptions': []}
    
    def verify_webhook_signature(self, payload, signature):
        """Verify webhook signature from Whop."""
        config = self.get_whop_config()
        if not config['webhook_secret']:
            return False
        
        expected_signature = hmac.new(
            config['webhook_secret'].encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def is_user_premium(self, access_token, user_id):
        """Check if user has an active premium subscription."""
        try:
            subscriptions = self.get_user_subscriptions(access_token, user_id)
            for subscription in subscriptions.get('subscriptions', []):
                if subscription.get('status') == 'active':
                    return True
            return False
        except:
            return False

# Decorator to require Whop authentication
def require_whop_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('whop_access_token'):
            return redirect(url_for('whop_auth'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to require premium subscription
def require_premium(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('whop_access_token'):
            return redirect(url_for('whop_auth'))
        
        whop = current_app.whop
        user_id = session.get('whop_user_id')
        access_token = session.get('whop_access_token')
        
        if not whop.is_user_premium(access_token, user_id):
            return redirect(url_for('upgrade_required'))
        
        return f(*args, **kwargs)
    return decorated_function
