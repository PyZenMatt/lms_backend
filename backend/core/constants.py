"""
Core constants for the school platform application.
These constants centralize commonly used choices and values across the platform.
"""

# User Role Choices
USER_ROLES = (
    ('student', 'Student'),
    ('teacher', 'Teacher'),
    ('admin', 'Administrator'),
)

# Course Categories
COURSE_CATEGORIES = (
    ('painting', 'Painting'),
    ('drawing', 'Drawing'),
    ('digital_art', 'Digital Art'),
    ('sculpture', 'Sculpture'),
    ('mixed_media', 'Mixed Media'),
    ('art_history', 'Art History'),
    ('portfolio', 'Portfolio Development'),
)

# Exercise Types
EXERCISE_TYPES = (
    ('practice', 'Practice Exercise'),
    ('assignment', 'Assignment'),
    ('project', 'Project'),
    ('quiz', 'Quiz'),
    ('portfolio_piece', 'Portfolio Piece'),
)

# Submission Status Choices
SUBMISSION_STATUS = (
    ('pending', 'Pending Review'),
    ('approved', 'Approved'),
    ('needs_revision', 'Needs Revision'),
    ('rejected', 'Rejected'),
)

# Transaction Types for TeoCoin
TEOCOIN_TRANSACTION_TYPES = (
    ('earned_lesson', 'Lesson Completion'),
    ('earned_exercise', 'Exercise Completion'),
    ('earned_course', 'Course Completion'),
    ('earned_achievement', 'Achievement Unlocked'),
    ('transfer_sent', 'Transfer Sent'),
    ('transfer_received', 'Transfer Received'),
    ('manual_reward', 'Manual Reward'),
    ('bulk_reward', 'Bulk Reward'),
    ('admin_adjustment', 'Admin Adjustment'),
)

# Notification Types
NOTIFICATION_TYPES = (
    ('exercise_graded', 'Exercise Graded'),
    ('lesson_completed', 'Lesson Completed'),
    ('course_completed', 'Course Completed'),
    ('achievement_unlocked', 'Achievement Unlocked'),
    ('teacher_approved', 'Teacher Approved'),
    ('teocoin_earned', 'TeoCoin Earned'),
    ('teocoin_transfer', 'TeoCoin Transfer'),
    ('course_enrollment', 'Course Enrollment'),
    ('system_announcement', 'System Announcement'),
)

# Achievement Types
ACHIEVEMENT_TYPES = (
    ('first_lesson', 'First Lesson Completed'),
    ('first_course', 'First Course Completed'),
    ('first_exercise', 'First Exercise Submitted'),
    ('streak_week', '7-Day Learning Streak'),
    ('streak_month', '30-Day Learning Streak'),
    ('master_student', 'Master Student (10 Courses)'),
    ('art_critic', 'Art Critic (100 Exercise Reviews)'),
    ('portfolio_master', 'Portfolio Master'),
    ('community_helper', 'Community Helper'),
    ('early_bird', 'Early Bird (Active before 8 AM)'),
    ('night_owl', 'Night Owl (Active after 10 PM)'),
)

# Course Difficulty Levels
DIFFICULTY_LEVELS = (
    ('beginner', 'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
    ('expert', 'Expert'),
)

# File Upload Types
ALLOWED_FILE_TYPES = (
    ('image/jpeg', 'JPEG Image'),
    ('image/png', 'PNG Image'),
    ('image/gif', 'GIF Image'),
    ('image/webp', 'WebP Image'),
    ('application/pdf', 'PDF Document'),
    ('video/mp4', 'MP4 Video'),
    ('video/webm', 'WebM Video'),
)

# Platform Settings
DEFAULT_SETTINGS = {
    'TEOCOIN_LESSON_REWARD': 10,
    'TEOCOIN_EXERCISE_REWARD': 15,
    'TEOCOIN_COURSE_COMPLETION_REWARD': 50,
    'TEOCOIN_ACHIEVEMENT_REWARD': 25,
    'MAX_FILE_SIZE_MB': 10,
    'SESSION_TIMEOUT_MINUTES': 60,
    'NOTIFICATION_RETENTION_DAYS': 30,
}

# API Response Messages
API_MESSAGES = {
    'SUCCESS': 'Operation completed successfully',
    'INVALID_REQUEST': 'Invalid request data',
    'PERMISSION_DENIED': 'Permission denied',
    'NOT_FOUND': 'Resource not found',
    'UNAUTHORIZED': 'Authentication required',
    'SERVER_ERROR': 'Internal server error',
    'VALIDATION_ERROR': 'Validation failed',
}

# Pagination Settings
PAGINATION = {
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 100,
    'PAGE_SIZE_QUERY_PARAM': 'page_size',
}

# Cache Keys
CACHE_KEYS = {
    'USER_PROFILE': 'user_profile_{user_id}',
    'COURSE_LIST': 'course_list_{category}_{page}',
    'LESSON_CONTENT': 'lesson_content_{lesson_id}',
    'EXERCISE_SUBMISSIONS': 'exercise_submissions_{exercise_id}',
    'TEOCOIN_BALANCE': 'teocoin_balance_{user_id}',
    'NOTIFICATION_COUNT': 'notification_count_{user_id}',
}

# Cache Timeouts (in seconds)
CACHE_TIMEOUTS = {
    'SHORT': 300,    # 5 minutes
    'MEDIUM': 3600,  # 1 hour
    'LONG': 86400,   # 24 hours
}
