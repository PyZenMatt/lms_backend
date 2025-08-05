from django.urls import path, include
from rest_framework.routers import DefaultRouter

# === COURSES ===
from courses.views.courses import (
    CourseListCreateView, 
    CourseDetailView, 
    CreateCourseAPI,
    CourseListAPIView,
    CourseDetailAPIView
)


from courses.views.enrollments import (
    PurchaseCourseView,
    CourseEnrollmentView,
    StudentEnrolledCoursesView,
    TeacherCourseStudentsView
)
from courses.views.hybrid_payment import HybridPaymentView

# === PAYMENTS ===
from courses.views.payments import (
    CreatePaymentIntentView,
    ConfirmPaymentView, 
    PaymentSummaryView,
    TeoCoinDiscountStatusView
)

# === DEBUG ===
from courses.debug_stripe import DebugStripeView

# === LESSONS ===
from courses.views.lessons import (
    CourseLessonsView,
    AllLessonsWithCourseView,
    LessonCreateAssignView,
    AssignLessonToCourseAPI,
    LessonDetailView,
    LessonExercisesView,
    LessonViewSet,
    MarkLessonCompleteView
)

# === EXERCISES ===
from courses.views.exercises import (
    CreateExerciseView,
    SubmitExerciseView,
    ReviewExerciseView,
    MySubmissionView,           
    AssignedReviewsView,        
    SubmissionDetailView,   
    SubmissionHistoryView, 
    ReviewHistoryView,        
    ExerciseSubmissionsView,
    ExerciseDebugReviewersView,
    ExerciseDetailView
)

# === PENDING COURSES ===
from courses.views.pending import PendingCoursesView, ApproveCourseView, RejectCourseView

# === TEACHER CHOICE ===
from courses.api.teacher_choice_api import TeacherChoiceViewSet, TeacherPreferenceViewSet

# Setup router for ViewSets
router = DefaultRouter()
router.register(r'teacher-choices', TeacherChoiceViewSet, basename='teacher-choices')
router.register(r'teacher-preferences', TeacherPreferenceViewSet, basename='teacher-preferences')


urlpatterns = [
    # === TEACHER CHOICE API ===
    path('api/', include(router.urls)),
    
    # === COURSES ===
    path('courses/', CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/<int:course_id>/purchase/', PurchaseCourseView.as_view(), name='course-purchase'),

    # === HYBRID PAYMENT ===
    path('courses/<int:course_id>/hybrid-payment/', HybridPaymentView.as_view(), name='hybrid-payment'),
    
    # === NEW COURSE SERVICE ENDPOINTS ===
    path('courses-service/', CourseListAPIView.as_view(), name='course-list-api'),
    path('courses-service/<int:pk>/', CourseDetailAPIView.as_view(), name='course-detail-api'),

    # === ENROLLMENTS ===
    path('courses/<int:course_id>/enroll/', CourseEnrollmentView.as_view(), name='course-enroll'),
    path('student/enrolled_courses/', StudentEnrolledCoursesView.as_view(), name='student-enrolled-courses'),
    path('teacher/courses/students/', TeacherCourseStudentsView.as_view(), name='teacher-course-students'),

    # === LESSONS ===
    path('courses/<int:course_id>/lessons/', CourseLessonsView.as_view(), name='course-lessons'),
    path('lessons/all/', AllLessonsWithCourseView.as_view(), name='all-lessons-with-course'),
    path('lessons/create/', LessonCreateAssignView.as_view(), name='create-assign-lesson'),
    path('lessons/<int:lesson_id>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:lesson_id>/exercises/', LessonExercisesView.as_view(), name='lesson-exercises'),
    path('lessons/<int:lesson_id>/mark_complete/', MarkLessonCompleteView.as_view(), name='lesson-mark-complete'),

    # === EXERCISES ===
    path('exercises/create/', CreateExerciseView.as_view(), name='create-exercise'),
    path('exercises/<int:exercise_id>/submit/', SubmitExerciseView.as_view(), name='submit-exercise'),
    path('exercises/<int:submission_id>/review/', ReviewExerciseView.as_view(), name='review-exercise'),
    # --- Nuovi endpoint peer review ---
    path('exercises/<int:exercise_id>/my_submission/', MySubmissionView.as_view(), name='my-exercise-submission'),
    path('reviews/assigned/', AssignedReviewsView.as_view(), name='assigned-reviews'),
    path('submissions/<int:submission_id>/', SubmissionDetailView.as_view(), name='submission-detail'),
    path('exercises/submissions/', SubmissionHistoryView.as_view(), name='submission-history'),
    path('reviews/history/', ReviewHistoryView.as_view(), name='review-history'),
    path('exercises/<int:exercise_id>/submissions/', ExerciseSubmissionsView.as_view(), name='exercise-submissions'), # opzionale
    path('exercises/<int:exercise_id>/debug_reviewers/', ExerciseDebugReviewersView.as_view(), name='exercise-debug-reviewers'),
    path('exercises/<int:id>/', ExerciseDetailView.as_view(), name='exercise-detail'),

    # === PENDING COURSES ===
    path('pending-courses/', PendingCoursesView.as_view(), name='pending-courses'),
    path('approve-course/<int:course_id>/', ApproveCourseView.as_view(), name='approve-course'),
    path('reject-course/<int:course_id>/', RejectCourseView.as_view(), name='reject-course'),
    
    # === FIAT PAYMENTS ===
    path('debug/stripe/', DebugStripeView.as_view(), name='debug-stripe'),
    path('courses/<int:course_id>/create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('courses/<int:course_id>/confirm-payment/', ConfirmPaymentView.as_view(), name='confirm-payment'),
    path('courses/<int:course_id>/payment-summary/', PaymentSummaryView.as_view(), name='payment-summary'),
    path('courses/<int:course_id>/discount-status/', TeoCoinDiscountStatusView.as_view(), name='teocoin-discount-status'),
]
