from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView
from courses.models import Lesson, Course, LessonCompletion, CourseEnrollment
from courses.serializers import LessonSerializer, LessonListSerializer
from users.permissions import IsTeacher, IsAdminOrApprovedTeacherOrReadOnly


class CourseLessonsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = request.user
        # Allow access if user is staff, superuser, course teacher, or course is approved
        if not (user.is_staff or user.is_superuser or course.teacher == user) and not course.is_approved:
            raise PermissionDenied("Corso non approvato")
        lessons = Lesson.objects.filter(course_id=course_id).order_by('order')
        serializer = LessonListSerializer(lessons, many=True)
        return Response(serializer.data)


class AllLessonsWithCourseView(generics.ListAPIView):
    queryset = Lesson.objects.select_related('course').all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]  # Rimuovi IsAdminOrApprovedTeacherOrReadOnly per permettere agli studenti di segnare come completata

    def get_queryset(self):
        # ✅ OTTIMIZZATO - Prevent N+1 queries with select_related and prefetch_related
        return Lesson.objects.select_related('course', 'course__teacher').prefetch_related(
            'exercises', 'completions'
        )

    @action(detail=True, methods=['post'], url_path='mark_complete', url_name='mark-complete', permission_classes=[IsAuthenticated])
    def mark_complete(self, request, pk=None):
        # pk sarà sempre l'id della lezione grazie a url_path
        lesson = get_object_or_404(Lesson, pk=pk)
        course = lesson.course
        if not course:
            return Response({"detail": "Lezione non associata a nessun corso."}, status=status.HTTP_400_BAD_REQUEST)
        if request.user not in course.students.all():
            return Response(
                {"detail": "Non sei iscritto a questo corso."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Registra il completamento della lezione per lo studente
        completion, created = LessonCompletion.objects.get_or_create(student=request.user, lesson=lesson)

        # Import here to avoid circular imports
        try:
            from rewards.automation import reward_system
            
            # The automated reward system will be triggered by the signal
            # But we can also check course completion here for immediate feedback
            total_lessons = course.lessons.count()
            completed_lessons = LessonCompletion.objects.filter(
                student=request.user,
                lesson__course=course
            ).count()
            
            if completed_lessons >= total_lessons:
                # Mark course as completed and trigger completion bonus
                enrollment, _ = CourseEnrollment.objects.get_or_create(
                    student=request.user,
                    course=course
                )
                
                if not enrollment.completed:
                    enrollment.completed = True
                    enrollment.save()
                    
                    return Response({
                        "completed": True, 
                        "course_completed": True,
                        "detail": "🎓 Congratulazioni! Hai completato tutto il corso!"
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "completed": True,
                        "course_completed": True, 
                        "detail": "Corso già completato!"
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "completed": True, 
                    "course_completed": False,
                    "progress": f"{completed_lessons}/{total_lessons}",
                    "detail": f"Lezione completata! Progresso: {completed_lessons}/{total_lessons}"
                }, status=status.HTTP_200_OK)
                
        except ImportError:
            # Fallback if reward system is not available
            total = Lesson.objects.filter(course=course).count()
            if lesson.order == total:
                return Response(
                    {"completed": True, "detail": "Corso completato!"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"completed": True, "detail": "Lezione segnata come completata."},
                    status=status.HTTP_200_OK
                )


class LessonCreateAssignView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request):
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({"error": "L'ID del corso è obbligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, id=course_id, teacher=request.user)

        # Create a new data dict instead of copying request.data to avoid pickle issues with files
        data = {
            'title': request.data.get('title'),
            'content': request.data.get('content'),
            'duration': request.data.get('duration'),
            'lesson_type': request.data.get('lesson_type'),
            'course': course.id,
        }
        
        # Handle file separately if present
        if 'video_file' in request.FILES:
            data['video_file'] = request.FILES['video_file']

        serializer = LessonSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            lesson = serializer.save(teacher=request.user)
            course.lessons.add(lesson)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignLessonToCourseAPI(generics.UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsTeacher]

    def perform_update(self, serializer):
        course = serializer.validated_data.get('course')
        if course.teacher != self.request.user:
            raise PermissionDenied("Non sei il proprietario di questo corso")
        serializer.save()


class LessonDetailView(RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer  # Use the detailed serializer
    lookup_field = 'id'
    lookup_url_kwarg = 'lesson_id'

    def get(self, request, *args, **kwargs):
        lesson = self.get_object()
        course = lesson.course
        user = request.user
        # Allow access if user is staff, superuser, course teacher, or course is approved
        if course and not (user.is_staff or user.is_superuser or course.teacher == user) and not course.is_approved:
            raise PermissionDenied("Corso non approvato")
        response = super().get(request, *args, **kwargs)
        completed = False
        if request.user.is_authenticated:
            from courses.models import LessonCompletion
            completed = LessonCompletion.objects.filter(student=request.user, lesson=lesson).exists()
        data = response.data
        data['completed'] = completed
        return Response(data)


class LessonExercisesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        course = lesson.course
        user = request.user
        # Allow access if user is staff, superuser, course teacher, or course is approved
        if course and not (user.is_staff or user.is_superuser or course.teacher == user) and not course.is_approved:
            raise PermissionDenied("Corso non approvato")
        exercises = lesson.exercises.all()
        data = [{"id": e.id, "title": e.title, "description": e.description} for e in exercises]
        return Response(data, status=status.HTTP_200_OK)


class MarkLessonCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        course = lesson.course
        if not course:
            return Response({"detail": "Lezione non associata a nessun corso."}, status=status.HTTP_400_BAD_REQUEST)
        if request.user not in course.students.all():
            return Response({"detail": "Non sei iscritto a questo corso."}, status=status.HTTP_400_BAD_REQUEST)
        LessonCompletion.objects.get_or_create(student=request.user, lesson=lesson)
        total = Lesson.objects.filter(course=course).count()
        if lesson.order == total:
            return Response({"completed": True, "detail": "Corso completato!"}, status=status.HTTP_200_OK)
        else:
            return Response({"completed": True, "detail": "Lezione segnata come completata."}, status=status.HTTP_200_OK)
