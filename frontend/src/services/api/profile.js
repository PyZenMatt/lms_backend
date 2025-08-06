import api from '../core/axiosClient';

// Profile Settings API
export const fetchUserSettings = async () => {
  return api.get('profile/settings/');
};

export const updateUserSettings = async (settings) => {
  return api.put('profile/settings/', settings);
};

// Profile Progress API
export const fetchUserProgress = async () => {
  return api.get('profile/progress/');
};

export const fetchUserAchievements = async () => {
  return api.get('profile/achievements/');
};

export const fetchCourseProgress = async (courseId) => {
  return api.get(`courses/${courseId}/progress/`);
};

// Helper function to transform backend data to frontend format
export const transformProgressData = (backendData) => {
  return {
    overall: {
      coursesCompleted: backendData.completed_courses_count || 0,
      coursesInProgress: backendData.in_progress_courses_count || 0,
      totalCourses: backendData.total_courses_count || 0,
      hoursLearned: backendData.total_hours || 0,
      averageScore: backendData.average_score || 0
    },
    categories: backendData.categories?.map(cat => ({
      id: cat.slug || (cat.name || '').toLowerCase(),
      name: cat.name,
      icon: getCategoryIcon(cat.name),
      progress: Math.round(cat.progress_percentage || 0),
      coursesCompleted: cat.completed_courses || 0,
      totalCourses: cat.total_courses || 0,
      color: getCategoryColor(cat.name)
    })) || [],
    achievements: backendData.achievements?.map(achievement => ({
      id: achievement.id,
      title: achievement.title,
      description: achievement.description,
      earned: achievement.earned,
      earnedDate: achievement.earned_date,
      progress: achievement.progress,
      icon: achievement.icon || 'award',
      color: achievement.color || '#feca57'
    })) || [],
    recentActivity: backendData.recent_activities?.map(activity => ({
      id: activity.id,
      type: activity.type,
      title: activity.title,
      date: activity.date,
      score: activity.score,
      icon: getActivityIcon(activity.type)
    })) || []
  };
};

// Helper function to get category icons
const getCategoryIcon = (categoryName) => {
  const iconMap = {
    'Pittura': 'image',
    'Scultura': 'box',
    'Disegno': 'edit-3',
    'Arte Digitale': 'monitor',
    'Fotografia': 'camera',
    'Ceramica': 'circle',
    'Gioielleria': 'star'
  };
  return iconMap[categoryName] || 'book';
};

// Helper function to get category colors
const getCategoryColor = (categoryName) => {
  const colorMap = {
    'Pittura': '#ff6b6b',
    'Scultura': '#4ecdc4',
    'Disegno': '#45b7d1',
    'Arte Digitale': '#f9ca24',
    'Fotografia': '#a55eea',
    'Ceramica': '#26de81',
    'Gioielleria': '#fd79a8'
  };
  return colorMap[categoryName] || '#6c5ce7';
};

// Helper function to get activity icons
const getActivityIcon = (activityType) => {
  const iconMap = {
    'course_completed': 'check-circle',
    'lesson_completed': 'play-circle',
    'exercise_completed': 'edit',
    'achievement_earned': 'award',
    'quiz_completed': 'help-circle'
  };
  return iconMap[activityType] || 'activity';
};

// Transform settings data for frontend use
export const transformSettingsData = (backendData) => {
  return {
    emailNotifications: backendData.email_notifications ?? true,
    pushNotifications: backendData.push_notifications ?? false,
    courseReminders: backendData.course_reminders ?? true,
    weeklyDigest: backendData.weekly_digest ?? true,
    marketingEmails: backendData.marketing_emails ?? false,
    theme: backendData.theme || 'light',
    language: backendData.language || 'it',
    timezone: backendData.timezone || 'Europe/Rome',
    privacy: {
      showProfile: backendData.privacy?.show_profile ?? true,
      showProgress: backendData.privacy?.show_progress ?? false,
      showAchievements: backendData.privacy?.show_achievements ?? true
    }
  };
};

// Transform settings data for backend submission
export const transformSettingsForBackend = (frontendData) => {
  return {
    email_notifications: frontendData.emailNotifications,
    push_notifications: frontendData.pushNotifications,
    course_reminders: frontendData.courseReminders,
    weekly_digest: frontendData.weeklyDigest,
    marketing_emails: frontendData.marketingEmails,
    theme: frontendData.theme,
    language: frontendData.language,
    timezone: frontendData.timezone,
    privacy: {
      show_profile: frontendData.privacy.showProfile,
      show_progress: frontendData.privacy.showProgress,
      show_achievements: frontendData.privacy.showAchievements
    }
  };
};
