#!/usr/bin/env python3
"""
Comprehensive Test Suite for Whop Gamify App
Run this to ensure everything works correctly
"""

import os
import sys
import unittest
from datetime import datetime, date
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, DailyProgress, Achievement, UserAchievement
from app import xp_required_for_level, total_xp_for_level, level_from_xp, calculate_level_progress

class TestWhopGamifyApp(unittest.TestCase):
    """Test cases for the Whop Gamify App."""
    
    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test user
        self.test_user = User(
            whop_user_id='test_user_123',
            username='TestUser',
            email='test@example.com',
            xp=0,
            level=0,
            points=0,
            streak_count=0
        )
        db.session.add(self.test_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_app_creation(self):
        """Test that the app is created correctly."""
        self.assertIsNotNone(app)
        self.assertTrue(app.config['TESTING'])
    
    def test_database_models(self):
        """Test database models."""
        # Test User model
        user = User.query.filter_by(whop_user_id='test_user_123').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'TestUser')
        self.assertEqual(user.xp, 0)
        self.assertEqual(user.level, 0)
    
    def test_xp_system(self):
        """Test XP and leveling system."""
        # Test XP calculations
        self.assertEqual(xp_required_for_level(1), 100)
        self.assertEqual(xp_required_for_level(2), 200)
        self.assertEqual(xp_required_for_level(5), 500)
        
        # Test total XP calculations
        self.assertEqual(total_xp_for_level(1), 100)
        self.assertEqual(total_xp_for_level(2), 300)  # 100 + 200
        self.assertEqual(total_xp_for_level(3), 600)  # 100 + 200 + 300
        
        # Test level from XP
        self.assertEqual(level_from_xp(0), 0)
        self.assertEqual(level_from_xp(100), 1)
        self.assertEqual(level_from_xp(300), 2)
        self.assertEqual(level_from_xp(600), 3)
        
        # Test level progress
        progress, needed = calculate_level_progress(150, 1)
        self.assertEqual(progress, 50)  # 150 - 100
        self.assertEqual(needed, 200)   # XP needed for level 2
    
    def test_daily_progress(self):
        """Test daily progress tracking."""
        today = date.today()
        
        # Create daily progress
        daily = DailyProgress(
            user_id=self.test_user.id,
            date=today,
            actions_completed=0,
            quests_completed=0
        )
        db.session.add(daily)
        db.session.commit()
        
        # Test daily progress
        daily = DailyProgress.query.filter_by(user_id=self.test_user.id, date=today).first()
        self.assertIsNotNone(daily)
        self.assertEqual(daily.actions_completed, 0)
        self.assertEqual(daily.quests_completed, 0)
        
        # Test incrementing actions
        daily.actions_completed += 1
        db.session.commit()
        
        daily = DailyProgress.query.filter_by(user_id=self.test_user.id, date=today).first()
        self.assertEqual(daily.actions_completed, 1)
    
    def test_achievements(self):
        """Test achievement system."""
        # Create test achievement
        achievement = Achievement(
            name="Test Achievement",
            description="A test achievement",
            icon="🎯",
            xp_reward=50,
            points_reward=10,
            requirement_type="level",
            requirement_value=1
        )
        db.session.add(achievement)
        db.session.commit()
        
        # Test achievement creation
        achievement = Achievement.query.filter_by(name="Test Achievement").first()
        self.assertIsNotNone(achievement)
        self.assertEqual(achievement.xp_reward, 50)
        self.assertEqual(achievement.requirement_type, "level")
    
    def test_user_achievements(self):
        """Test user achievement system."""
        # Create achievement
        achievement = Achievement(
            name="Test Achievement",
            description="A test achievement",
            icon="🎯",
            xp_reward=50,
            points_reward=10,
            requirement_type="level",
            requirement_value=1
        )
        db.session.add(achievement)
        db.session.commit()
        
        # Create user achievement
        user_achievement = UserAchievement(
            user_id=self.test_user.id,
            achievement_id=achievement.id
        )
        db.session.add(user_achievement)
        db.session.commit()
        
        # Test user achievement
        user_achievement = UserAchievement.query.filter_by(
            user_id=self.test_user.id,
            achievement_id=achievement.id
        ).first()
        self.assertIsNotNone(user_achievement)
    
    def test_home_page(self):
        """Test home page loads correctly."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Whop Gamify', response.data)
    
    def test_login_page(self):
        """Test login page loads correctly."""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data)
    
    def test_demo_login(self):
        """Test demo login functionality."""
        response = self.app.post('/demo_login', 
                               json={'username': 'DemoUser', 'email': 'demo@example.com'},
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_api_earn_xp(self):
        """Test XP earning API endpoint."""
        # Login user first
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(self.test_user.id)
            sess['_fresh'] = True
        
        response = self.app.post('/api/earn_xp',
                               json={'action_type': 'action', 'amount': 10},
                               content_type='application/json')
        
        # Should redirect to login since we're not properly authenticated
        self.assertIn(response.status_code, [200, 302])
    
    def test_api_complete_quest(self):
        """Test quest completion API endpoint."""
        # Login user first
        with self.app.session_transaction() as sess:
            sess['_user_id'] = str(self.test_user.id)
            sess['_fresh'] = True
        
        response = self.app.post('/api/complete_quest',
                               json={'quest_type': 'daily'},
                               content_type='application/json')
        
        # Should redirect to login since we're not properly authenticated
        self.assertIn(response.status_code, [200, 302])
    
    def test_error_handling(self):
        """Test error handling."""
        # Test 404 page
        response = self.app.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
    
    def test_static_files(self):
        """Test static files are accessible."""
        response = self.app.get('/static/css/style.css')
        self.assertEqual(response.status_code, 200)
        
        response = self.app.get('/static/js/app.js')
        self.assertEqual(response.status_code, 200)

def run_tests():
    """Run all tests."""
    print("Running Whop Gamify App Tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWhopGamifyApp)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print results
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All tests passed! Your app is ready for deployment.")
        return True
    else:
        print(f"{len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for failure in result.failures:
            print(f"FAIL: {failure[0]}")
            print(f"     {failure[1]}")
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(f"       {error[1]}")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
