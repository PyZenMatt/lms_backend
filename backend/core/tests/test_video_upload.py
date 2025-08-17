#!/usr/bin/env python
"""
Test script per verificare l'upload di video nelle lezioni
"""
import os
import sys

# Aggiungi il path del progetto Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')

import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from courses.models import Course, Lesson, User
from courses.serializers import LessonSerializer
from rest_framework.test import APIClient
from django.test import TestCase

def test_lesson_video_upload():
    print("🎥 Testando l'upload di video per le lezioni...")
    
    # Verifica che la directory media esista
    from django.conf import settings
    media_root = settings.MEDIA_ROOT
    video_dir = os.path.join(media_root, 'lesson_videos')
    
    print(f"📁 MEDIA_ROOT: {media_root}")
    print(f"📁 Video directory: {video_dir}")
    
    if not os.path.exists(media_root):
        os.makedirs(media_root)
        print("✅ Creata directory media")
    
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
        print("✅ Creata directory lesson_videos")
    
    # Verifica i permessi di scrittura
    try:
        test_file = os.path.join(video_dir, 'test_permissions.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ Permessi di scrittura OK")
    except Exception as e:
        print(f"❌ Errore permessi di scrittura: {e}")
        return
    
    # Verifica modello Lesson
    print("\n📋 Testando il modello Lesson...")
    try:
        # Crea un utente teacher di test
        teacher = User.objects.filter(role='teacher').first()
        if not teacher:
            print("❌ Nessun teacher trovato nel database")
            return
        
        # Crea un corso di test
        course = Course.objects.filter(teacher=teacher).first()
        if not course:
            print("❌ Nessun corso trovato per il teacher")
            return
            
        print(f"✅ Teacher: {teacher.username}")
        print(f"✅ Course: {course.title}")
        
        # Simula un file video
        video_content = b"fake video content for testing"
        video_file = SimpleUploadedFile(
            "test_video.mp4",
            video_content,
            content_type="video/mp4"
        )
        
        # Crea una lezione con video
        lesson_data = {
            'title': 'Test Video Lesson',
            'content': 'This is a test lesson with video',
            'lesson_type': 'video',
            'duration': 30,
            'course': course.id,
            'video_file': video_file
        }
        
        # Test del serializer
        from rest_framework.request import Request
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post('/lessons/create/')
        request.user = teacher
        
        serializer = LessonSerializer(data=lesson_data, context={'request': request})
        if serializer.is_valid():
            lesson = serializer.save(teacher=teacher)
            print(f"✅ Lezione creata: {lesson.title}")
            print(f"✅ Video file path: {lesson.video_file.name}")
            print(f"✅ Video file URL: {lesson.video_file.url}")
            
            # Verifica che il file esista fisicamente
            full_path = os.path.join(settings.MEDIA_ROOT, lesson.video_file.name)
            if os.path.exists(full_path):
                print("✅ File video salvato correttamente sul filesystem")
            else:
                print("❌ File video NON trovato sul filesystem")
                
            # Cleanup
            lesson.delete()
            
        else:
            print(f"❌ Errori di validazione: {serializer.errors}")
            
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

def test_api_lesson_creation():
    print("\n🌐 Testando l'API REST per la creazione di lezioni...")
    
    # Trova un teacher
    teacher = User.objects.filter(role='teacher').first()
    if not teacher:
        print("❌ Nessun teacher trovato")
        return
        
    # Trova un corso del teacher
    course = Course.objects.filter(teacher=teacher).first()
    if not course:
        print("❌ Nessun corso trovato")
        return
    
    # Setup client API
    client = APIClient()
    client.force_authenticate(user=teacher)
    
    # Simula un file video
    video_content = b"fake video content for API testing"
    video_file = SimpleUploadedFile(
        "api_test_video.mp4",
        video_content,
        content_type="video/mp4"
    )
    
    # Prepara i dati
    data = {
        'title': 'API Test Video Lesson',
        'content': 'This is a test lesson created via API',
        'lesson_type': 'video',
        'duration': 45,
        'course_id': course.id,
        'video_file': video_file
    }
    
    # Fai la richiesta POST
    response = client.post('/api/v1/lessons/create/', data, format='multipart')
    
    if response.status_code == 201:
        lesson_data = response.json()
        print(f"✅ Lezione creata via API: {lesson_data['title']}")
        print(f"✅ Video URL: {lesson_data.get('video_file_url', 'N/A')}")
        
        # Verifica che il file esista
        if 'video_file_url' in lesson_data and lesson_data['video_file_url']:
            print("✅ URL del video restituito correttamente")
        else:
            print("❌ URL del video non restituito")
            
        # Cleanup
        if 'id' in lesson_data:
            Lesson.objects.filter(id=lesson_data['id']).delete()
            
    else:
        print(f"❌ Errore API: Status {response.status_code}")
        print(f"❌ Risposta: {response.content.decode()}")

if __name__ == "__main__":
    test_lesson_video_upload()
    test_api_lesson_creation()
