/**
 * 🔧 Mock Activity API Service
 * 
 * Provides mock activity data when backend endpoints are not available
 */

const generateMockActivities = () => {
  const activityTypes = [
    { type: 'course_enrolled', icon: '📚', color: 'primary' },
    { type: 'exercise_completed', icon: '✅', color: 'success' },
    { type: 'lesson_viewed', icon: '👁️', color: 'info' },
    { type: 'teocoin_earned', icon: '🪙', color: 'warning' },
    { type: 'review_submitted', icon: '📝', color: 'secondary' },
    { type: 'achievement_unlocked', icon: '🏆', color: 'warning' }
  ];

  const users = [
    'Marco Rossi', 'Sofia Chen', 'Alessandro Torre', 'Elena Bianchi', 
    'David Kumar', 'Francesca Marino', 'Roberto Silva', 'Anna Kowalski'
  ];

  const courses = [
    'React Fundamentals', 'JavaScript ES6+', 'Node.js Backend', 
    'CSS Grid & Flexbox', 'Python Django', 'Vue.js Basics'
  ];

  const activities = [];
  const now = new Date();

  for (let i = 0; i < 15; i++) {
    const activityType = activityTypes[Math.floor(Math.random() * activityTypes.length)];
    const user = users[Math.floor(Math.random() * users.length)];
    const course = courses[Math.floor(Math.random() * courses.length)];
    
    const timestamp = new Date(now.getTime() - (i * 5 * 60000)); // 5 minutes apart
    
    let description = '';
    switch (activityType.type) {
      case 'course_enrolled':
        description = `enrolled in "${course}"`;
        break;
      case 'exercise_completed':
        description = `completed an exercise in "${course}"`;
        break;
      case 'lesson_viewed':
        description = `viewed a lesson in "${course}"`;
        break;
      case 'teocoin_earned':
        description = `earned ${Math.floor(Math.random() * 50) + 10} TeoCoins`;
        break;
      case 'review_submitted':
        description = `submitted a peer review`;
        break;
      case 'achievement_unlocked':
        description = `unlocked the "Study Streak" achievement`;
        break;
    }

    activities.push({
      id: `mock_${i}`,
      user: {
        name: user,
        avatar: `/api/placeholder/40/40?text=${user.split(' ').map(n => n[0]).join('')}`
      },
      activity_type: activityType.type,
      description,
      timestamp: timestamp.toISOString(),
      metadata: {
        course: course,
        icon: activityType.icon,
        color: activityType.color
      }
    });
  }

  return activities;
};

export const mockActivityAPI = {
  /**
   * Mock activity feed endpoint
   */
  async getActivityFeed() {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const activities = generateMockActivities();
    
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        activities,
        total: activities.length,
        has_more: false,
        next_cursor: null
      })
    };
  },

  /**
   * Mock real-time activity subscription
   */
  subscribeToActivities(callback) {
    // Simulate real-time updates every 30 seconds
    const interval = setInterval(() => {
      const newActivity = generateMockActivities().slice(0, 1)[0];
      newActivity.id = `live_${Date.now()}`;
      newActivity.timestamp = new Date().toISOString();
      
      callback({
        type: 'new_activity',
        data: newActivity
      });
    }, 30000);

    return () => clearInterval(interval);
  }
};

export default mockActivityAPI;
