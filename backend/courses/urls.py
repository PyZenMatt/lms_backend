# === TEACHER CHOICE ===
from courses.api.teacher_choice_api import (
    TeacherChoiceViewSet,
    TeacherPreferenceViewSet,
)

# === DEBUG ===
from courses.debug_stripe import DebugStripeView

# === COURSES ===
from courses.views.courses import (
    CourseDetailAPIView,
    CourseDetailView,
    CourseListAPIView,
    CourseListCreateView,
    TeacherCoursesView,
)
from courses.views.enrollments import (
    CourseEnrollmentView,
    PurchaseCourseView,
    StudentEnrolledCoursesView,
    TeacherCourseStudentsView,
)

# === EXERCISES ===
from courses.views.exercises import (
    AssignedReviewsView,
    CreateExerciseView,
    ExerciseDebugReviewersView,
    ExerciseDetailView,
    ExerciseSubmissionsView,
    MySubmissionView,
    ReviewExerciseView,
    ReviewHistoryView,
    SubmissionDetailForReviewerView,
    SubmissionDetailView,
    SubmissionHistoryView,
    SubmitExerciseView,
)
from courses.views.hybrid_payment import HybridPaymentView

# === LESSONS ===
from courses.views.lessons import (
    AllLessonsWithCourseView,
    CourseLessonsView,
    LessonCreateAssignView,
    LessonDetailView,
    LessonExercisesView,
    MarkLessonCompleteView,
)

# === PAYMENTS ===
from courses.views.payments import (
    ConfirmPaymentView,
    CreatePaymentIntentView,
    PaymentSummaryView,
    TeoCoinDiscountStatusView,
)

# === PENDING COURSES ===
from courses.views.pending import (
    ApproveCourseView,
    PendingCoursesView,
    RejectCourseView,
)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

# Setup router for ViewSets
router = DefaultRouter()
router.register(r"teacher-choices", TeacherChoiceViewSet, basename="teacher-choices")
router.register(
    r"teacher-preferences", TeacherPreferenceViewSet, basename="teacher-preferences"
)


urlpatterns = [
    # === TEACHER CHOICE API ===
    # Expose router directly at module root so that when this file is
    # included under `path("api/v1/", include("courses.urls"))` the
    # resulting endpoints are `/api/v1/teacher-choices/...` (no double `api/`).
    path("", include(router.urls)),
    # === COURSES ===
    path("courses/", CourseListCreateView.as_view(), name="course-list-create"),
    path("courses/<int:pk>/", CourseDetailView.as_view(), name="course-detail"),
    path(
        "courses/<int:course_id>/purchase/",
        PurchaseCourseView.as_view(),
        name="course-purchase",
    ),
    # === HYBRID PAYMENT ===
    path(
        "courses/<int:course_id>/hybrid-payment/",
        HybridPaymentView.as_view(),
        name="hybrid-payment",
    ),
    # === NEW COURSE SERVICE ENDPOINTS ===
    path("courses-service/", CourseListAPIView.as_view(), name="course-list-api"),
    path(
        "courses-service/<int:pk>/",
        CourseDetailAPIView.as_view(),
        name="course-detail-api",
    ),
    # === ENROLLMENTS ===
    path(
        "courses/<int:course_id>/enroll/",
        CourseEnrollmentView.as_view(),
        name="course-enroll",
    ),
    path(
        "student/enrolled_courses/",
        StudentEnrolledCoursesView.as_view(),
        name="student-enrolled-courses",
    ),
    path(
        "teacher/courses/students/",
        TeacherCourseStudentsView.as_view(),
        name="teacher-course-students",
    ),
    # Teacher's own courses list for Studio frontend
    path("teacher/courses/", TeacherCoursesView.as_view(), name="teacher-courses"),
    # === LESSONS ===
    path(
        "courses/<int:course_id>/lessons/",
        CourseLessonsView.as_view(),
        name="course-lessons",
    ),
    path(
        "lessons/all/",
        AllLessonsWithCourseView.as_view(),
        name="all-lessons-with-course",
    ),
    path(
        "lessons/create/", LessonCreateAssignView.as_view(), name="create-assign-lesson"
    ),
    path("lessons/<int:lesson_id>/", LessonDetailView.as_view(), name="lesson-detail"),
    path(
        "lessons/<int:lesson_id>/exercises/",
        LessonExercisesView.as_view(),
        name="lesson-exercises",
    ),
    path(
        "lessons/<int:lesson_id>/mark_complete/",
        MarkLessonCompleteView.as_view(),
        name="lesson-mark-complete",
    ),
    # === EXERCISES ===
    path("exercises/create/", CreateExerciseView.as_view(), name="create-exercise"),
    path(
        "exercises/<int:exercise_id>/submit/",
        SubmitExerciseView.as_view(),
        name="submit-exercise",
    ),
    path(
        "exercises/<int:exercise_id>/review/",
        ReviewExerciseView.as_view(),
        name="review-exercise",
    ),
    # Compatibility aliases: allow posting review by submission_id or legacy patterns
    path(
        "submissions/<int:submission_id>/review/",
        ReviewExerciseView.as_view(),
        name="review-by-submission",
    ),
    path(
        "reviews/<int:submission_id>/submit/",
        ReviewExerciseView.as_view(),
        name="review-submit-compat",
    ),
    path(
        "reviews/<int:submission_id>/",
        ReviewExerciseView.as_view(),
        name="review-submit-compat2",
    ),
    # --- Nuovi endpoint peer review ---
    path(
        "exercises/<int:exercise_id>/my_submission/",
        MySubmissionView.as_view(),
        name="my-exercise-submission",
    ),
    path("reviews/assigned/", AssignedReviewsView.as_view(), name="assigned-reviews"),
    path(
        "submissions/<int:submission_id>/",
        SubmissionDetailView.as_view(),
        name="submission-detail",
    ),
    path(
        "submissions/<int:submission_id>/review-detail/",
        SubmissionDetailForReviewerView.as_view(),
        name="submission-detail-for-reviewer",
    ),
    path(
        "exercises/submissions/",
        SubmissionHistoryView.as_view(),
        name="submission-history",
    ),
    path("reviews/history/", ReviewHistoryView.as_view(), name="review-history"),
    path(
        "exercises/<int:exercise_id>/submissions/",
        ExerciseSubmissionsView.as_view(),
        name="exercise-submissions",
    ),  # opzionale
    path(
        "exercises/<int:exercise_id>/debug_reviewers/",
        ExerciseDebugReviewersView.as_view(),
        name="exercise-debug-reviewers",
    ),
    path("exercises/<int:id>/", ExerciseDetailView.as_view(), name="exercise-detail"),
    # === PENDING COURSES ===
    path("pending-courses/", PendingCoursesView.as_view(), name="pending-courses"),
    path(
        "approve-course/<int:course_id>/",
        ApproveCourseView.as_view(),
        name="approve-course",
    ),
    path(
        "reject-course/<int:course_id>/",
        RejectCourseView.as_view(),
        name="reject-course",
    ),
    # === FIAT PAYMENTS ===
    path("debug/stripe/", DebugStripeView.as_view(), name="debug-stripe"),
    path(
        "courses/<int:course_id>/create-payment-intent/",
        CreatePaymentIntentView.as_view(),
        name="create-payment-intent",
    ),
    path(
        "courses/<int:course_id>/confirm-payment/",
        ConfirmPaymentView.as_view(),
        name="confirm-payment",
    ),
    path(
        "courses/<int:course_id>/payment-summary/",
        PaymentSummaryView.as_view(),
        name="payment-summary",
    ),
    path(
        "courses/<int:course_id>/discount-status/",
        TeoCoinDiscountStatusView.as_view(),
        name="teocoin-discount-status",
    ),
]
