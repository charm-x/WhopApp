# Whop Gamify App

A gamification web application that transforms your Whop community into an engaging, level-based experience. Users can earn XP, level up, unlock achievements, and compete with others through various activities.

## Features

### 🎯 Core Gamification
- **XP System**: Earn experience points through various actions
- **Leveling**: Progressive leveling system with increasing XP requirements
- **Achievements**: Unlock special badges and rewards
- **Points System**: Earn redeemable points for exclusive rewards

### 🏆 User Experience
- **Beautiful UI**: Modern, responsive design with smooth animations
- **Level-up Animations**: Celebratory effects when reaching new levels
- **Progress Tracking**: Visual progress bars and statistics
- **Real-time Updates**: Instant feedback for XP gains and level ups

### 📊 Analytics & Progress
- **Daily Progress**: Track daily activities and streaks
- **Weekly Quests**: Complete weekly challenges for bonus rewards
- **Achievement System**: Multiple achievement categories
- **User Profiles**: Comprehensive user statistics and progress

## Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation

1. **Clone or download the project**
   ```bash
   cd whop_gamify_app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///whop_gamify.db

# XP Configuration
XP_PER_ACTION=5
XP_PER_DAILY_QUEST=25
XP_PER_WEEKLY_QUEST=100
POINTS_PER_DAILY_QUEST=1
POINTS_PER_WEEKLY_QUEST=5
```

### XP System Configuration

The app uses a progressive XP system:
- **Level 1**: 100 XP required
- **Level 2**: 100 + 200 = 300 XP total
- **Level 3**: 100 + 200 + 300 = 600 XP total
- **Level N**: Sum of (level × 100) for all levels

## API Endpoints

### User Actions
- `POST /api/earn_xp` - Earn XP through various actions
- `POST /api/complete_quest` - Complete daily or weekly quests

### Authentication
- `GET /login` - Login page
- `POST /demo_login` - Create demo user for testing
- `GET /logout` - Logout user

### Pages
- `GET /` - Landing page
- `GET /dashboard` - User dashboard
- `GET /profile` - User profile and achievements

## Whop Integration

### For Production Deployment

1. **Whop OAuth Integration**
   - Replace demo login with Whop's OAuth system
   - Use Whop's user management API
   - Implement proper webhook handling

2. **Database Setup**
   - Use PostgreSQL or MySQL for production
   - Set up proper database migrations
   - Configure connection pooling

3. **Environment Configuration**
   ```env
   WHOP_API_KEY=your-whop-api-key
   WHOP_WEBHOOK_SECRET=your-whop-webhook-secret
   DATABASE_URL=postgresql://user:pass@host/dbname
   ```

## Customization

### Adding New Achievement Types

1. **Create Achievement in Database**
   ```python
   achievement = Achievement(
       name="Custom Achievement",
       description="Complete a custom action",
       icon="🎯",
       xp_reward=50,
       points_reward=10,
       requirement_type="custom",
       requirement_value=1
   )
   ```

2. **Add Achievement Check Logic**
   ```python
   def check_custom_achievements(user):
       # Your custom achievement logic here
       pass
   ```

### Modifying XP System

Edit the XP calculation functions in `app.py`:

```python
def xp_required_for_level(level):
    # Customize XP requirements per level
    return level * 100  # Current: 100, 200, 300, etc.
```

### Styling Customization

Modify `static/css/style.css` to customize:
- Color scheme (CSS variables in `:root`)
- Animations and transitions
- Layout and spacing
- Typography

## File Structure

```
whop_gamify_app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── dashboard.html    # User dashboard
│   └── profile.html      # User profile
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Custom styles
    └── js/
        └── app.js        # JavaScript functionality
```

## Demo Features

The app includes a demo mode for testing:

1. **Demo Login**: Use "Try Demo" button to create a test user
2. **Sample Data**: Demo user starts with Level 5, 1250 XP, and 3-day streak
3. **Interactive Elements**: All XP earning and quest completion features work
4. **Animations**: Level-up effects and progress animations

## Deployment

### Local Development
```bash
python app.py
```

### Production Deployment

1. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

2. **Set up reverse proxy** (nginx)
3. **Configure SSL certificates**
4. **Set up monitoring and logging**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For questions or support:
- Create an issue in the repository
- Check the documentation
- Review the demo functionality

---

**Ready to gamify your Whop community?** Start with the demo and customize it for your needs!
