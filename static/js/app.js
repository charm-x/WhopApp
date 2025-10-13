// Custom JavaScript for Whop Gamify App

// Global app state
window.GamifyApp = {
    user: null,
    isAuthenticated: false,
    
    init: function() {
        this.checkAuth();
        this.setupEventListeners();
        this.loadUserData();
    },
    
    checkAuth: function() {
        const demoUser = sessionStorage.getItem('demo_user');
        if (demoUser) {
            this.user = JSON.parse(demoUser);
            this.isAuthenticated = true;
        }
    },
    
    setupEventListeners: function() {
        // Setup any global event listeners here
        document.addEventListener('DOMContentLoaded', () => {
            this.initAnimations();
        });
    },
    
    loadUserData: function() {
        if (this.isAuthenticated && this.user) {
            this.updateUserInterface();
        }
    },
    
    updateUserInterface: function() {
        // Update any user-specific UI elements
        const usernameElements = document.querySelectorAll('.user-username');
        usernameElements.forEach(el => {
            el.textContent = this.user.username;
        });
    },
    
    initAnimations: function() {
        // Initialize any animations
        this.animateCounters();
        this.animateProgressBars();
    },
    
    animateCounters: function() {
        const counters = document.querySelectorAll('.stat-number, .level-number');
        counters.forEach(counter => {
            const target = parseInt(counter.textContent);
            if (!isNaN(target)) {
                this.animateCounter(counter, 0, target, 1000);
            }
        });
    },
    
    animateCounter: function(element, start, end, duration) {
        const startTime = performance.now();
        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = Math.floor(start + (end - start) * progress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        };
        requestAnimationFrame(updateCounter);
    },
    
    animateProgressBars: function() {
        const progressBars = document.querySelectorAll('.xp-progress');
        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => {
                bar.style.width = width;
            }, 500);
        });
    },
    
    showNotification: function(message, type = 'success') {
        // Create a custom notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    },
    
    playSound: function(soundType) {
        // Play sound effects (you can add actual sound files)
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        if (soundType === 'levelup') {
            // Level up sound
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
            oscillator.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E5
            oscillator.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G5
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } else if (soundType === 'xp') {
            // XP earned sound
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(440, audioContext.currentTime); // A4
            oscillator.frequency.setValueAtTime(554.37, audioContext.currentTime + 0.1); // C#5
            
            gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        }
    },
    
    createParticleEffect: function(element, type = 'sparkle') {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        for (let i = 0; i < 10; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: fixed;
                width: 6px;
                height: 6px;
                background: ${type === 'sparkle' ? '#f59e0b' : '#10b981'};
                border-radius: 50%;
                pointer-events: none;
                z-index: 9999;
                left: ${centerX}px;
                top: ${centerY}px;
            `;
            
            document.body.appendChild(particle);
            
            // Animate particle
            const angle = (Math.PI * 2 * i) / 10;
            const distance = 50 + Math.random() * 50;
            const endX = centerX + Math.cos(angle) * distance;
            const endY = centerY + Math.sin(angle) * distance;
            
            particle.animate([
                { transform: 'translate(0, 0) scale(1)', opacity: 1 },
                { transform: `translate(${endX - centerX}px, ${endY - centerY}px) scale(0)`, opacity: 0 }
            ], {
                duration: 1000,
                easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
            }).onfinish = () => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            };
        }
    },
    
    // XP and leveling functions
    earnXP: function(amount, actionType = 'action') {
        if (!this.isAuthenticated) {
            this.showNotification('Please log in to earn XP!', 'warning');
            return;
        }
        
        fetch('/api/earn_xp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action_type: actionType,
                amount: amount
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.user.xp = data.new_xp;
                this.user.level = data.new_level;
                
                // Update session storage
                sessionStorage.setItem('demo_user', JSON.stringify(this.user));
                
                // Show XP notification
                this.showXPNotification(amount);
                
                // Play sound
                this.playSound('xp');
                
                // Update UI
                this.updateXPDisplay(data);
                
                // Check for level up
                if (data.level_up) {
                    setTimeout(() => {
                        this.showLevelUpModal(data.new_level);
                    }, 500);
                }
            }
        })
        .catch(error => {
            console.error('Error earning XP:', error);
            this.showNotification('Failed to earn XP. Please try again.', 'danger');
        });
    },
    
    completeQuest: function(questType) {
        if (!this.isAuthenticated) {
            this.showNotification('Please log in to complete quests!', 'warning');
            return;
        }
        
        fetch('/api/complete_quest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                quest_type: questType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.user.xp = data.new_xp;
                this.user.level = data.new_level;
                this.user.points = data.new_points;
                
                // Update session storage
                sessionStorage.setItem('demo_user', JSON.stringify(this.user));
                
                const amount = questType === 'daily' ? 25 : 100;
                this.showXPNotification(amount);
                this.playSound('xp');
                this.updateXPDisplay(data);
                
                if (data.level_up) {
                    setTimeout(() => {
                        this.showLevelUpModal(data.new_level);
                    }, 500);
                }
            }
        })
        .catch(error => {
            console.error('Error completing quest:', error);
            this.showNotification('Failed to complete quest. Please try again.', 'danger');
        });
    },
    
    showXPNotification: function(amount) {
        const toast = document.getElementById('xpToast');
        const xpAmount = document.getElementById('xpAmount');
        
        if (toast && xpAmount) {
            xpAmount.textContent = `+${amount}`;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    },
    
    showLevelUpModal: function(newLevel) {
        const modal = document.getElementById('levelUpModal');
        const levelSpan = document.getElementById('newLevel');
        
        if (modal && levelSpan) {
            levelSpan.textContent = newLevel;
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Play level up sound
            this.playSound('levelup');
            
            // Create particle effect
            const levelBadge = document.querySelector('.level-badge, .level-badge-large');
            if (levelBadge) {
                this.createParticleEffect(levelBadge, 'sparkle');
            }
        }
    },
    
    updateXPDisplay: function(data) {
        // Update XP counters
        const xpElements = document.querySelectorAll('.stat-number');
        if (xpElements.length > 0) {
            this.animateCounter(xpElements[0], parseInt(xpElements[0].textContent), data.new_xp, 500);
        }
        
        // Update level badges
        const levelElements = document.querySelectorAll('.level-number');
        levelElements.forEach(el => {
            this.animateCounter(el, parseInt(el.textContent), data.new_level, 500);
        });
        
        // Update progress bar
        const progressBar = document.querySelector('.xp-progress');
        if (progressBar && data.progress) {
            const progressPercent = (data.progress[0] / data.progress[1]) * 100;
            progressBar.style.width = progressPercent + '%';
            
            // Update progress text
            const xpText = document.querySelector('.xp-text');
            if (xpText) {
                xpText.innerHTML = `
                    <span class="current-xp">${data.progress[0]}</span> / 
                    <span class="needed-xp">${data.progress[1]}</span> XP 
                    <span class="xp-percent">(${progressPercent.toFixed(1)}%)</span>
                `;
            }
        }
    },
    
    // Utility functions
    formatNumber: function(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },
    
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    // Logout function
    logout: function() {
        // Clear client-side data
        sessionStorage.removeItem('demo_user');
        this.user = null;
        this.isAuthenticated = false;
        
        // Call server-side logout to clear session
        fetch('/logout', {
            method: 'GET',
            credentials: 'same-origin'
        }).then(() => {
            // Redirect to login page after server logout
            window.location.href = '/login';
        }).catch(() => {
            // Fallback: redirect even if server call fails
            window.location.href = '/login';
        });
    }
};

// Global functions for HTML onclick handlers
function earnXP(actionType, amount) {
    window.GamifyApp.earnXP(amount, actionType);
}

function completeQuest(questType) {
    window.GamifyApp.completeQuest(questType);
}

function logout() {
    window.GamifyApp.logout();
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.GamifyApp.init();
});

// Add some CSS for particles
const style = document.createElement('style');
style.textContent = `
    .particle {
        box-shadow: 0 0 10px currentColor;
    }
    
    .toast {
        backdrop-filter: blur(10px);
    }
    
    .modal-backdrop {
        backdrop-filter: blur(5px);
    }
`;
document.head.appendChild(style);
