from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json
import math
from functools import wraps
try:
    from whop_integration import WhopIntegration, require_whop_auth, require_premium
    WHOP_AVAILABLE = True
except ImportError:
    WHOP_AVAILABLE = False
    print("Warning: Whop integration not available. Install requests package for full functionality.")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///whop_gamify.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Whop integration
if WHOP_AVAILABLE:
    whop_integration = WhopIntegration(app)
else:
    whop_integration = None

# XP System Configuration
XP_PER_ACTION = 5
XP_PER_DAILY_QUEST = 25
XP_PER_WEEKLY_QUEST = 100
DAILY_QUEST_RESET_HOUR = 0  # Midnight
WEEKLY_QUEST_RESET_DAY = 0  # Sunday

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whop_user_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    streak_count = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    daily_progress = db.relationship('DailyProgress', backref='user', lazy=True)
    weekly_progress = db.relationship('WeeklyProgress', backref='user', lazy=True)
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)

class DailyProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    streak_count = db.Column(db.Integer, default=0)
    actions_completed = db.Column(db.Integer, default=0)
    quests_completed = db.Column(db.Integer, default=0)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'date'),)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.actions_completed = 0
        self.quests_completed = 0

class WeeklyProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    week_start = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    actions_completed = db.Column(db.Integer, default=0)
    quests_completed = db.Column(db.Integer, default=0)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'week_start'),)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    xp_reward = db.Column(db.Integer, default=0)
    points_reward = db.Column(db.Integer, default=0)
    requirement_type = db.Column(db.String(50))  # 'level', 'xp', 'streak', 'actions'
    requirement_value = db.Column(db.Integer)

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id'),)

# XP and Leveling Functions (adapted from original)
def xp_required_for_level(level):
    """XP required to advance from level-1 to level (level >= 1)."""
    if level <= 0:
        return 0
    return level * 100

def total_xp_for_level(level):
    """Total XP required to reach a given level."""
    if level <= 0:
        return 0
    return sum(i * 100 for i in range(1, level + 1))

def level_from_xp(xp):
    """Compute current level from XP using the increasing-cost model."""
    if xp <= 0:
        return 0
    
    level = 0
    while total_xp_for_level(level + 1) <= xp:
        level += 1
    return level

def calculate_level_progress(xp, level):
    """Calculate progress towards next level."""
    base_xp = total_xp_for_level(level)
    need = xp_required_for_level(level + 1)
    progress = max(0, xp - base_xp)
    return progress, need

# Utility Functions
def update_user_level(user):
    """Update user's level based on current XP."""
    new_level = level_from_xp(user.xp)
    if new_level > user.level:
        user.level = new_level
        return True  # Level up!
    return False

def add_xp(user, amount, action_type="action"):
    """Add XP to user and check for level up."""
    user.xp += amount
    user.last_activity = datetime.utcnow()
    
    level_up = update_user_level(user)
    
    # Update daily progress
    today = datetime.utcnow().date()
    daily = DailyProgress.query.filter_by(user_id=user.id, date=today).first()
    if not daily:
        daily = DailyProgress(user_id=user.id, date=today)
        db.session.add(daily)
        db.session.flush()  # Ensure the object is saved before using it
    
    if action_type == "action":
        daily.actions_completed += 1
    elif action_type == "quest":
        daily.quests_completed += 1
    
    db.session.commit()
    return level_up

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/home')
def home():
    """Home page with app information."""
    return render_template('index.html')

@app.route('/login')
def login():
    # In a real Whop app, this would integrate with Whop's OAuth
    # For demo purposes, we'll create a simple login
    return render_template('login.html')

@app.route('/demo_login', methods=['POST'])
def demo_login():
    """Create a demo user for testing purposes."""
    data = request.get_json()
    username = data.get('username', 'DemoUser')
    email = data.get('email', 'demo@example.com')
    
    # Check if demo user already exists
    demo_user = User.query.filter_by(whop_user_id='demo_user').first()
    
    if not demo_user:
        # Create demo user
        demo_user = User(
            whop_user_id='demo_user',
            username=username,
            email=email,
            xp=1250,
            level=5,
            points=25,
            streak_count=3
        )
        db.session.add(demo_user)
        db.session.commit()
    
    login_user(demo_user)
    return jsonify({'success': True, 'redirect': url_for('dashboard')})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

# Whop OAuth Routes
@app.route('/auth/whop')
def whop_auth():
    """Initiate Whop OAuth flow."""
    if not WHOP_AVAILABLE or not whop_integration:
        return render_template('error.html', 
                             error="Whop integration is not available. Please contact the administrator.")
    try:
        auth_url = whop_integration.get_auth_url()
        return redirect(auth_url)
    except Exception as e:
        app.logger.error(f"Whop auth error: {str(e)}")
        return render_template('error.html', 
                             error="Whop authentication is not configured. Please contact the administrator.")

@app.route('/auth/whop/callback')
def whop_callback():
    """Handle Whop OAuth callback."""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            return render_template('error.html', error="Authorization code not provided")
        
        # Exchange code for token
        token_data = whop_integration.exchange_code_for_token(code)
        access_token = token_data['access_token']
        
        # Get user info
        user_data = whop_integration.get_user_info(access_token)
        
        # Create or update user
        user = User.query.filter_by(whop_user_id=user_data['id']).first()
        
        if not user:
            user = User(
                whop_user_id=user_data['id'],
                username=user_data.get('username', user_data.get('email', 'Unknown')),
                email=user_data.get('email', ''),
                xp=0,
                level=0,
                points=0,
                streak_count=0
            )
            db.session.add(user)
        else:
            # Update existing user info
            user.username = user_data.get('username', user.username)
            user.email = user_data.get('email', user.email)
        
        db.session.commit()
        
        # Store in session
        session['whop_access_token'] = access_token
        session['whop_user_id'] = user_data['id']
        session['whop_user_data'] = user_data
        
        # Login user
        login_user(user)
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        app.logger.error(f"Whop callback error: {str(e)}")
        return render_template('error.html', error="Authentication failed. Please try again.")

@app.route('/webhook/whop', methods=['POST'])
def whop_webhook():
    """Handle Whop webhooks."""
    try:
        signature = request.headers.get('X-Whop-Signature')
        payload = request.get_data()
        
        if not whop_integration.verify_webhook_signature(payload, signature):
            return 'Unauthorized', 401
        
        data = request.get_json()
        event_type = data.get('type')
        
        if event_type == 'user.created':
            handle_new_whop_user(data['data'])
        elif event_type == 'user.updated':
            handle_whop_user_update(data['data'])
        elif event_type == 'subscription.created':
            handle_subscription_created(data['data'])
        elif event_type == 'subscription.cancelled':
            handle_subscription_cancelled(data['data'])
        
        return 'OK', 200
        
    except Exception as e:
        app.logger.error(f"Webhook error: {str(e)}")
        return 'Error', 500

def handle_new_whop_user(user_data):
    """Handle new user creation from webhook."""
    user = User.query.filter_by(whop_user_id=user_data['id']).first()
    if not user:
        user = User(
            whop_user_id=user_data['id'],
            username=user_data.get('username', user_data.get('email', 'Unknown')),
            email=user_data.get('email', ''),
            xp=0,
            level=0,
            points=0,
            streak_count=0
        )
        db.session.add(user)
        db.session.commit()

def handle_whop_user_update(user_data):
    """Handle user updates from webhook."""
    user = User.query.filter_by(whop_user_id=user_data['id']).first()
    if user:
        user.username = user_data.get('username', user.username)
        user.email = user_data.get('email', user.email)
        db.session.commit()

def handle_subscription_created(subscription_data):
    """Handle new subscription creation."""
    # You can add premium features here
    app.logger.info(f"New subscription created: {subscription_data}")

def handle_subscription_cancelled(subscription_data):
    """Handle subscription cancellation."""
    # You can remove premium features here
    app.logger.info(f"Subscription cancelled: {subscription_data}")

@app.route('/upgrade')
def upgrade_required():
    """Show upgrade page for premium features."""
    return render_template('upgrade.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    
    # Calculate level progress
    progress, needed = calculate_level_progress(user.xp, user.level)
    progress_percent = (progress / needed * 100) if needed > 0 else 0
    
    # Get today's progress
    today = datetime.utcnow().date()
    daily = DailyProgress.query.filter_by(user_id=user.id, date=today).first()
    
    # Get recent achievements
    recent_achievements = UserAchievement.query.filter_by(user_id=user.id).order_by(UserAchievement.unlocked_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         progress=progress, 
                         needed=needed, 
                         progress_percent=progress_percent,
                         daily=daily,
                         recent_achievements=recent_achievements)

@app.route('/profile')
@login_required
def profile():
    user = current_user
    
    # Get all achievements
    user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
    all_achievements = Achievement.query.all()
    
    # Create achievement status
    achievement_status = []
    for achievement in all_achievements:
        user_has = any(ua.achievement_id == achievement.id for ua in user_achievements)
        achievement_status.append({
            'achievement': achievement,
            'unlocked': user_has,
            'unlocked_at': next((ua.unlocked_at for ua in user_achievements if ua.achievement_id == achievement.id), None)
        })
    
    return render_template('profile.html', 
                         user=user, 
                         achievement_status=achievement_status)

@app.route('/api/earn_xp', methods=['POST'])
@login_required
def earn_xp():
    """API endpoint to earn XP through various actions."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        action_type = data.get('action_type', 'action')
        amount = data.get('amount', XP_PER_ACTION)
        
        # Validate amount
        if not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid amount'}), 400
        
        level_up = add_xp(current_user, int(amount), action_type)
        
        # Check for achievements
        check_achievements(current_user)
        
        return jsonify({
            'success': True,
            'new_xp': current_user.xp,
            'new_level': current_user.level,
            'level_up': level_up,
            'progress': calculate_level_progress(current_user.xp, current_user.level)
        })
    except Exception as e:
        app.logger.error(f"Error in earn_xp: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/complete_quest', methods=['POST'])
@login_required
def complete_quest():
    """Complete a daily or weekly quest."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        quest_type = data.get('quest_type', 'daily')
        
        if quest_type == 'daily':
            amount = XP_PER_DAILY_QUEST
            points = 1
        elif quest_type == 'weekly':
            amount = XP_PER_WEEKLY_QUEST
            points = 5
        else:
            return jsonify({'success': False, 'error': 'Invalid quest type'}), 400
        
        level_up = add_xp(current_user, amount, 'quest')
        current_user.points += points
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_xp': current_user.xp,
            'new_level': current_user.level,
            'new_points': current_user.points,
            'level_up': level_up
        })
    except Exception as e:
        app.logger.error(f"Error in complete_quest: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

def check_achievements(user):
    """Check if user has unlocked any new achievements."""
    achievements = Achievement.query.all()
    user_achievements = UserAchievement.query.filter_by(user_id=user.id).all()
    user_achievement_ids = [ua.achievement_id for ua in user_achievements]
    
    for achievement in achievements:
        if achievement.id in user_achievement_ids:
            continue
            
        unlocked = False
        if achievement.requirement_type == 'level' and user.level >= achievement.requirement_value:
            unlocked = True
        elif achievement.requirement_type == 'xp' and user.xp >= achievement.requirement_value:
            unlocked = True
        elif achievement.requirement_type == 'streak' and user.streak_count >= achievement.requirement_value:
            unlocked = True
        
        if unlocked:
            user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            db.session.add(user_achievement)
            
            # Award bonus XP and points
            if achievement.xp_reward > 0:
                user.xp += achievement.xp_reward
            if achievement.points_reward > 0:
                user.points += achievement.points_reward
    
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database and create sample data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create sample achievements
        if Achievement.query.count() == 0:
            achievements = [
                Achievement(name="First Steps", description="Reach level 1", icon="🎯", xp_reward=10, requirement_type="level", requirement_value=1),
                Achievement(name="Getting Started", description="Reach level 5", icon="⭐", xp_reward=25, requirement_type="level", requirement_value=5),
                Achievement(name="Rising Star", description="Reach level 10", icon="🌟", xp_reward=50, requirement_type="level", requirement_value=10),
                Achievement(name="XP Collector", description="Earn 1000 XP", icon="💎", xp_reward=100, requirement_type="xp", requirement_value=1000),
                Achievement(name="Streak Master", description="Maintain a 7-day streak", icon="🔥", xp_reward=75, requirement_type="streak", requirement_value=7),
            ]
            
            for achievement in achievements:
                db.session.add(achievement)
            
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
