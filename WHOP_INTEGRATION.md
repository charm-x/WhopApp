# Whop Integration Guide

This guide explains how to integrate the Whop Gamify App with Whop's platform for production use.

## Overview

The current app includes a demo login system for testing. For production deployment with Whop, you'll need to:

1. Replace the demo authentication with Whop's OAuth system
2. Integrate with Whop's user management API
3. Set up webhook handling for real-time updates
4. Configure proper database and hosting

## Whop OAuth Integration

### 1. Whop App Setup

1. **Create a Whop App**
   - Go to [Whop Developer Portal](https://dev.whop.com)
   - Create a new app
   - Note your `Client ID` and `Client Secret`

2. **Configure OAuth Settings**
   - Set redirect URI: `https://yourdomain.com/auth/whop/callback`
   - Enable required scopes: `user:read`, `user:write`

### 2. Update Authentication System

Replace the demo login with Whop OAuth:

```python
# Add to app.py
import requests
from urllib.parse import urlencode

WHOP_CLIENT_ID = os.environ.get('WHOP_CLIENT_ID')
WHOP_CLIENT_SECRET = os.environ.get('WHOP_CLIENT_SECRET')
WHOP_REDIRECT_URI = os.environ.get('WHOP_REDIRECT_URI')

@app.route('/auth/whop')
def whop_auth():
    """Initiate Whop OAuth flow."""
    params = {
        'client_id': WHOP_CLIENT_ID,
        'redirect_uri': WHOP_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'user:read user:write',
        'state': 'random_state_string'  # Use proper state management
    }
    
    auth_url = f"https://whop.com/oauth/authorize?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/auth/whop/callback')
def whop_callback():
    """Handle Whop OAuth callback."""
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Exchange code for access token
    token_data = {
        'client_id': WHOP_CLIENT_ID,
        'client_secret': WHOP_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': WHOP_REDIRECT_URI
    }
    
    response = requests.post('https://whop.com/oauth/token', data=token_data)
    token_info = response.json()
    
    access_token = token_info['access_token']
    
    # Get user info from Whop
    user_response = requests.get(
        'https://api.whop.com/v1/user',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    user_data = user_response.json()
    
    # Create or update user in your database
    user = User.query.filter_by(whop_user_id=user_data['id']).first()
    
    if not user:
        user = User(
            whop_user_id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            xp=0,
            level=0,
            points=0,
            streak_count=0
        )
        db.session.add(user)
    else:
        # Update existing user info
        user.username = user_data['username']
        user.email = user_data['email']
    
    db.session.commit()
    login_user(user)
    
    return redirect(url_for('dashboard'))
```

### 3. Environment Variables

Add to your `.env` file:

```env
# Whop Integration
WHOP_CLIENT_ID=your_whop_client_id
WHOP_CLIENT_SECRET=your_whop_client_secret
WHOP_REDIRECT_URI=https://yourdomain.com/auth/whop/callback
WHOP_WEBHOOK_SECRET=your_webhook_secret
```

## Whop API Integration

### User Management

```python
# Add to app.py
import requests

def get_whop_user_info(access_token):
    """Get user information from Whop API."""
    response = requests.get(
        'https://api.whop.com/v1/user',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    return response.json()

def update_whop_user(access_token, user_data):
    """Update user information in Whop."""
    response = requests.patch(
        'https://api.whop.com/v1/user',
        headers={'Authorization': f'Bearer {access_token}'},
        json=user_data
    )
    return response.json()
```

### Webhook Integration

```python
# Add to app.py
import hmac
import hashlib

@app.route('/webhook/whop', methods=['POST'])
def whop_webhook():
    """Handle Whop webhooks."""
    signature = request.headers.get('X-Whop-Signature')
    payload = request.get_data()
    
    # Verify webhook signature
    expected_signature = hmac.new(
        WHOP_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return 'Unauthorized', 401
    
    # Process webhook data
    data = request.get_json()
    event_type = data.get('type')
    
    if event_type == 'user.created':
        # Handle new user creation
        handle_new_user(data['data'])
    elif event_type == 'user.updated':
        # Handle user updates
        handle_user_update(data['data'])
    
    return 'OK', 200

def handle_new_user(user_data):
    """Handle new user creation from webhook."""
    user = User(
        whop_user_id=user_data['id'],
        username=user_data['username'],
        email=user_data['email'],
        xp=0,
        level=0,
        points=0,
        streak_count=0
    )
    db.session.add(user)
    db.session.commit()

def handle_user_update(user_data):
    """Handle user updates from webhook."""
    user = User.query.filter_by(whop_user_id=user_data['id']).first()
    if user:
        user.username = user_data.get('username', user.username)
        user.email = user_data.get('email', user.email)
        db.session.commit()
```

## Database Migration

### Update User Model

```python
# Update User model in app.py
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whop_user_id = db.Column(db.String(100), unique=True, nullable=False)
    whop_access_token = db.Column(db.Text)  # Store access token
    whop_refresh_token = db.Column(db.Text)  # Store refresh token
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    streak_count = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    whop_subscription_status = db.Column(db.String(50))  # Track subscription
    whop_plan_id = db.Column(db.String(100))  # Track plan
```

## Production Deployment

### 1. Database Setup

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb whop_gamify

# Update DATABASE_URL
DATABASE_URL=postgresql://username:password@localhost/whop_gamify
```

### 2. Environment Configuration

```env
# Production Environment
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-production-key

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Whop Integration
WHOP_CLIENT_ID=your_production_client_id
WHOP_CLIENT_SECRET=your_production_client_secret
WHOP_REDIRECT_URI=https://yourdomain.com/auth/whop/callback
WHOP_WEBHOOK_SECRET=your_production_webhook_secret
```

### 3. Deployment with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 4. Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Testing Integration

### 1. Test OAuth Flow

1. Start your app locally
2. Visit `/auth/whop`
3. Complete OAuth flow
4. Verify user creation in database

### 2. Test Webhooks

Use ngrok for local webhook testing:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 5000

# Use ngrok URL in Whop webhook settings
# https://abc123.ngrok.io/webhook/whop
```

### 3. Test API Endpoints

```bash
# Test XP earning
curl -X POST http://localhost:5000/api/earn_xp \
  -H "Content-Type: application/json" \
  -d '{"action_type": "action", "amount": 10}'

# Test quest completion
curl -X POST http://localhost:5000/api/complete_quest \
  -H "Content-Type: application/json" \
  -d '{"quest_type": "daily"}'
```

## Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **Token Storage**: Securely store access tokens
3. **Webhook Verification**: Always verify webhook signatures
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Input Validation**: Validate all user inputs
6. **SQL Injection**: Use parameterized queries (SQLAlchemy handles this)

## Monitoring and Logging

```python
# Add logging to app.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/whop_gamify.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Whop Gamify startup')
```

## Support and Resources

- [Whop Developer Documentation](https://dev.whop.com/docs)
- [Whop API Reference](https://dev.whop.com/api)
- [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Ready to deploy?** Follow this guide step by step to integrate your gamification app with Whop's platform!
