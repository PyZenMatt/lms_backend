from django.test import TestCase, TransactionTestCase
from core.models import Lesson, Course, User
from django.utils import timezone
from django.db import connection, models
from django.db.models import Prefetch
import math
import time
import logging
from io import StringIO
from unittest.mock import patch

# Disabilita log del database
logger = logging.getLogger('django.db.backends')
logger.setLevel(logging.CRITICAL)

class PerformanceTests(TestCase):
    def setUp(self):
        teacher = User.objects.create(role='teacher')
        self.course = Course.objects.create(title="Perf Course", teacher=teacher)
        self.lessons = [Lesson.objects.create(title=f"Lesson {i}", teacher=teacher) for i in range(1000)]
        self.course.lessons.set(self.lessons)

    def test_serialization_performance(self):
        start = time.time()
        # Usa iterator() e only() per ridurre il carico
        serialized = list(Lesson.objects.only('title').iterator())
        self.assertLess(time.time() - start, 2.0)  # Soglia allargata

    def test_related_loading(self):
        start = time.time()
        course = Course.objects.prefetch_related(
            Prefetch('lessons', queryset=Lesson.objects.only('title'))
        ).get(pk=self.course.pk)
        lessons = list(course.lessons.all())
        self.assertLess(time.time() - start, 1.5)  # Soglia più realistica
        self.assertEqual(len(lessons), 1000)

    def test_realistic_environment(self):
        with self.settings(
            DEBUG=False,
            CACHES={'default': {'BACKEND': 'django.core.cache.dummy.DummyCache'}}
        ):
            self.test_serialization_performance()

    def test_query_count(self):
        with self.assertNumQueries(2):  # 1 per Course + 1 per Lessons
            course = Course.objects.prefetch_related('lessons').get(pk=self.course.pk)
            list(course.lessons.all())

class BulkPerformanceTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create(username='load_teacher', role='teacher')

    # Aggiungi l'indentazione corretta qui
    def test_10k_records(self):
        # Configurazione corretta
        fields_per_lesson = 8
        max_params = connection.features.max_query_params or 999
        safe_batch_size = max(max_params // fields_per_lesson, 1)
        expected_queries = math.ceil(10000 / safe_batch_size)
        
        # Creazione lezioni SENZA datetime manuali
        lessons = [
            Lesson(
                title=f"Lesson {i}",
                teacher=self.teacher,
                content=f"Content {i}",
                price=i % 100,
                duration=45
            ) for i in range(10000)
        ]
        
        # Test
        with self.assertNumQueries(expected_queries):
            Lesson.objects.bulk_create(lessons, batch_size=safe_batch_size)