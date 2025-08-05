# TeoArt School Platform - Database Documentation

## Database Overview

The TeoArt School Platform uses SQLite as the primary database for development and can be easily migrated to PostgreSQL for production. The database design follows Django ORM conventions with proper relationships and constraints.

## Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      User       │    │   UserSettings  │    │  UserProgress   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │───▶│ id (PK)         │    │ id (PK)         │
│ username        │    │ user_id (FK)    │    │ user_id (FK)    │◀──┐
│ email           │    │ email_notify    │    │ courses_enrolled│   │
│ password        │    │ privacy_settings│    │ courses_completed│   │
│ role            │    │ theme           │    │ lessons_completed│   │
│ is_approved     │    │ language        │    │ average_score   │   │
│ teo_coins       │    │ created_at      │    │ last_activity   │   │
│ created_at      │    │ updated_at      │    │ updated_at      │   │
│ updated_at      │    └─────────────────┘    └─────────────────┘   │
└─────────────────┘                                                │
         │                                                         │
         ▼                                                         │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│     Course      │    │     Lesson      │    │    Exercise     │   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤   │
│ id (PK)         │───▶│ id (PK)         │───▶│ id (PK)         │   │
│ title           │    │ course_id (FK)  │    │ lesson_id (FK)  │   │
│ description     │    │ title           │    │ title           │   │
│ category        │    │ content         │    │ description     │   │
│ level           │    │ order           │    │ exercise_type   │   │
│ teocoin_reward  │    │ duration        │    │ content         │   │
│ teacher_id (FK) │    │ created_at      │    │ max_score       │   │
│ created_at      │    │ updated_at      │    │ created_at      │   │
│ updated_at      │    └─────────────────┘    │ updated_at      │   │
└─────────────────┘                           └─────────────────┘   │
         │                                                         │
         ▼                                                         │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│ CourseEnrollment│    │LessonCompletion │    │ExerciseSubmission│   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤   │
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │   │
│ student_id (FK) │    │ student_id (FK) │    │ student_id (FK) │───┘
│ course_id (FK)  │    │ lesson_id (FK)  │    │ exercise_id (FK)│
│ enrolled_at     │    │ completed_at    │    │ submission      │
│ completed       │    │ score           │    │ score           │
│ completion_date │    │ time_spent      │    │ submitted_at    │
│ progress        │    └─────────────────┘    │ graded_at       │
└─────────────────┘                           │ feedback        │
                                               └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│TeoCoinTransaction│    │   Achievement   │    │  Notification   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ user_id (FK)    │    │ user_id (FK)    │    │ user_id (FK)    │
│ amount          │    │ achievement_type│    │ message         │
│ transaction_type│    │ course_id (FK)  │    │ notification_type│
│ description     │    │ earned_at       │    │ related_object_id│
│ recipient_id(FK)│    │ progress        │    │ is_read         │
│ created_at      │    │ metadata        │    │ created_at      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Models

### User Model
Extended Django's AbstractUser with platform-specific fields.

```python
class User(AbstractUser):
    email = EmailField(unique=True)
    role = CharField(choices=USER_ROLES, default='student')
    is_approved = BooleanField(default=False)  # For teacher approval
    teo_coins = IntegerField(default=0)
    bio = TextField(blank=True)
    profile_image = ImageField(upload_to='profiles/', blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**Indexes:**
- `email` (unique)
- `role`
- `is_approved`
- `created_at`

**Constraints:**
- Email must be unique
- Username must be unique
- Role must be in predefined choices

### UserSettings Model
User-specific configuration and preferences.

```python
class UserSettings(Model):
    user = OneToOneField(User, on_delete=CASCADE)
    email_notifications = BooleanField(default=True)
    push_notifications = BooleanField(default=True)
    privacy_settings = JSONField(default=dict)
    theme = CharField(max_length=20, default='light')
    language = CharField(max_length=10, default='en')
    timezone = CharField(max_length=50, default='UTC')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### UserProgress Model
Tracks user learning progress and statistics.

```python
class UserProgress(Model):
    user = OneToOneField(User, on_delete=CASCADE)
    total_courses_enrolled = IntegerField(default=0)
    total_courses_completed = IntegerField(default=0)
    total_lessons_completed = IntegerField(default=0)
    total_exercises_completed = IntegerField(default=0)
    average_score = FloatField(default=0.0)
    streak_days = IntegerField(default=0)
    last_activity_date = DateTimeField(null=True, blank=True)
    achievements_earned = IntegerField(default=0)
    total_teocoins_earned = IntegerField(default=0)
    updated_at = DateTimeField(auto_now=True)
```

## Course System Models

### Course Model
Main course entity containing metadata and configuration.

```python
class Course(Model):
    title = CharField(max_length=200)
    description = TextField()
    category = CharField(choices=COURSE_CATEGORIES)
    level = CharField(choices=COURSE_LEVELS)
    teocoin_reward = IntegerField(default=0)
    teacher = ForeignKey(User, on_delete=CASCADE, related_name='created_courses')
    thumbnail = ImageField(upload_to='course_thumbnails/', blank=True)
    is_published = BooleanField(default=False)
    max_enrollments = IntegerField(null=True, blank=True)
    duration_hours = IntegerField(default=0)
    prerequisites = ManyToManyField('self', blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**Indexes:**
- `category`
- `level`
- `teacher`
- `is_published`
- `created_at`

### Lesson Model
Individual lessons within courses.

```python
class Lesson(Model):
    course = ForeignKey(Course, on_delete=CASCADE, related_name='lessons')
    title = CharField(max_length=200)
    content = TextField()
    order = IntegerField()
    lesson_type = CharField(choices=LESSON_TYPES)
    duration_minutes = IntegerField(default=0)
    video_url = URLField(blank=True)
    materials = JSONField(default=list)  # File attachments, links
    is_mandatory = BooleanField(default=True)
    teocoin_reward = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**Indexes:**
- `course`
- `order`
- `lesson_type`

### Exercise Model
Practice exercises and assignments.

```python
class Exercise(Model):
    lesson = ForeignKey(Lesson, on_delete=CASCADE, related_name='exercises')
    title = CharField(max_length=200)
    description = TextField()
    exercise_type = CharField(choices=EXERCISE_TYPES)
    content = JSONField()  # Exercise data (questions, prompts, etc.)
    max_score = IntegerField(default=100)
    time_limit_minutes = IntegerField(null=True, blank=True)
    attempts_allowed = IntegerField(default=3)
    teocoin_reward = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

## Enrollment and Progress Models

### CourseEnrollment Model
Tracks student enrollment in courses.

```python
class CourseEnrollment(Model):
    student = ForeignKey(User, on_delete=CASCADE)
    course = ForeignKey(Course, on_delete=CASCADE)
    enrolled_at = DateTimeField(auto_now_add=True)
    completed = BooleanField(default=False)
    completion_date = DateTimeField(null=True, blank=True)
    progress_percentage = FloatField(default=0.0)
    last_accessed = DateTimeField(auto_now=True)
```

**Indexes:**
- `student`
- `course`
- `completed`
- `enrolled_at`

**Constraints:**
- Unique together: `student`, `course`

### LessonCompletion Model
Tracks individual lesson completions.

```python
class LessonCompletion(Model):
    student = ForeignKey(User, on_delete=CASCADE)
    lesson = ForeignKey(Lesson, on_delete=CASCADE)
    completed_at = DateTimeField(auto_now_add=True)
    score = FloatField(null=True, blank=True)
    time_spent_minutes = IntegerField(default=0)
    notes = TextField(blank=True)
```

**Indexes:**
- `student`
- `lesson`
- `completed_at`

**Constraints:**
- Unique together: `student`, `lesson`

### ExerciseSubmission Model
Tracks exercise submissions and grading.

```python
class ExerciseSubmission(Model):
    student = ForeignKey(User, on_delete=CASCADE)
    exercise = ForeignKey(Exercise, on_delete=CASCADE)
    submission_data = JSONField()  # Student's answers/work
    score = FloatField(null=True, blank=True)
    max_score = IntegerField()
    submitted_at = DateTimeField(auto_now_add=True)
    graded_at = DateTimeField(null=True, blank=True)
    graded_by = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True)
    feedback = TextField(blank=True)
    attempt_number = IntegerField(default=1)
```

**Indexes:**
- `student`
- `exercise`
- `submitted_at`
- `graded_at`

## Rewards System Models

### TeoCoinTransaction Model
Records all TeoCoin transactions.

```python
class TeoCoinTransaction(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='teocoin_transactions')
    transaction_type = CharField(choices=TEOCOIN_TRANSACTION_TYPES)
    amount = IntegerField()
    description = TextField()
    recipient = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True)
    related_object_type = ForeignKey(ContentType, on_delete=SET_NULL, null=True)
    related_object_id = PositiveIntegerField(null=True)
    blockchain_tx_hash = CharField(max_length=66, blank=True)  # Ethereum tx hash
    is_blockchain_confirmed = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

**Indexes:**
- `user`
- `transaction_type`
- `created_at`
- `blockchain_tx_hash`

### Achievement Model
Tracks user achievements and badges.

```python
class Achievement(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='achievements')
    achievement_type = CharField(choices=ACHIEVEMENT_TYPES)
    course = ForeignKey(Course, on_delete=CASCADE, null=True, blank=True)
    earned_at = DateTimeField(auto_now_add=True)
    progress = IntegerField(default=100)  # For progressive achievements
    metadata = JSONField(default=dict)  # Additional achievement data
```

**Indexes:**
- `user`
- `achievement_type`
- `course`
- `earned_at`

**Constraints:**
- Unique together: `user`, `achievement_type`, `course` (where applicable)

## Communication Models

### Notification Model
System notifications for users.

```python
class Notification(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='notifications')
    title = CharField(max_length=200)
    message = TextField()
    notification_type = CharField(choices=NOTIFICATION_TYPES)
    related_object_type = ForeignKey(ContentType, on_delete=SET_NULL, null=True)
    related_object_id = PositiveIntegerField(null=True)
    is_read = BooleanField(default=False)
    priority = CharField(choices=NOTIFICATION_PRIORITIES, default='normal')
    action_url = URLField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
    read_at = DateTimeField(null=True, blank=True)
```

**Indexes:**
- `user`
- `notification_type`
- `is_read`
- `created_at`
- `priority`

## Database Optimization

### Query Optimization Strategies

1. **Select Related**: Use `select_related()` for foreign key relationships
2. **Prefetch Related**: Use `prefetch_related()` for many-to-many and reverse foreign key relationships
3. **Database Indexes**: Strategic indexing on frequently queried fields
4. **Query Caching**: Cache expensive queries using Django's cache framework

### Common Query Patterns

```python
# Optimized course listing with related data
courses = Course.objects.select_related('teacher')\
    .prefetch_related('lessons', 'enrollments')\
    .filter(is_published=True)

# User progress with related achievements
user_progress = UserProgress.objects.select_related('user')\
    .prefetch_related('user__achievements__course')\
    .get(user=user)

# Transaction history with related objects
transactions = TeoCoinTransaction.objects.select_related('recipient')\
    .filter(user=user)\
    .order_by('-created_at')
```

### Database Constraints and Validation

```sql
-- User email uniqueness
ALTER TABLE users_user ADD CONSTRAINT unique_email UNIQUE (email);

-- Course enrollment uniqueness
ALTER TABLE courses_courseenrollment 
ADD CONSTRAINT unique_student_course UNIQUE (student_id, course_id);

-- Positive TeoCoin amounts
ALTER TABLE rewards_teocointf ADD CONSTRAINT positive_amount 
CHECK (amount > 0);

-- Valid lesson ordering
ALTER TABLE courses_lesson ADD CONSTRAINT positive_order 
CHECK ("order" > 0);
```

## Migration Strategy

### Development to Production Migration

1. **Data Export**: Export development data using Django fixtures
2. **Schema Migration**: Run migrations on production database
3. **Data Import**: Import cleaned production data
4. **Index Creation**: Create performance indexes
5. **Constraint Validation**: Verify all constraints are satisfied

### Backup and Recovery

```bash
# Database backup
python manage.py dumpdata --natural-foreign --natural-primary > backup.json

# Specific app backup
python manage.py dumpdata users > users_backup.json

# Database restore
python manage.py loaddata backup.json
```

### Database Monitoring

Key metrics to monitor:
- Query execution time
- Database connection count
- Index usage statistics
- Storage space utilization
- Lock contention
- Slow query log analysis

This database design provides a robust foundation for the TeoArt School Platform with proper normalization, indexing, and relationship management.
