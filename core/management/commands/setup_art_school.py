#!/usr/bin/env python3
"""
Script per popolare il database con corsi, lezioni ed esercizi di esempio
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.db import transaction
from users.models import User
from courses.models import Course, Lesson, Exercise

def create_sample_data():
    """Crea dati di esempio per corsi, lezioni ed esercizi"""
    
    print("🎨 Creazione dati di esempio per la scuola d'arte...")
    
    # Trova o crea un teacher
    try:
        teacher = User.objects.filter(role='teacher').first()
        if not teacher:
            teacher = User.objects.create_user(
                username='prof_artista',
                email='prof@arteschool.it',
                password='password123',
                first_name='Marco',
                last_name='Artisti',
                role='teacher'
            )
            print(f"✅ Creato teacher: {teacher.username}")
        else:
            print(f"📚 Usando teacher esistente: {teacher.username}")
    except Exception as e:
        print(f"❌ Errore nella creazione del teacher: {e}")
        return

    # Dati dei corsi da creare
    courses_data = [
        {
            'title': 'Disegno Base: Fondamenti e Tecniche',
            'description': '''Un corso completo per imparare le basi del disegno artistico. 
            Inizieremo con la matita, impareremo le proporzioni, le ombre e le luci.
            Perfetto per principianti che vogliono sviluppare una solida base artistica.''',
            'category': 'disegno',
            'lessons': [
                {
                    'title': 'Introduzione al Disegno: Materiali e Postura',
                    'content': '''In questa prima lezione scopriremo:
                    • I materiali essenziali per il disegno (matite, carta, gomme)
                    • Come tenere correttamente la matita
                    • La postura corretta per disegnare
                    • Prime linee e tratti di base
                    
                    Ricorda: il disegno è una skill che si sviluppa con la pratica costante!''',
                    'lesson_type': 'theory',
                    'duration': 45,
                    'exercise': {
                        'title': 'Esercizio di Linee e Tratti Base',
                        'description': '''Disegna una pagina completa con:
                        • 10 linee rette parallele
                        • 10 cerchi della stessa dimensione
                        • 10 spirali in senso orario
                        • Gradazione da chiaro a scuro con la matita
                        
                        Concentrati sulla consistenza dei tratti.''',
                        'exercise_type': 'practical',
                        'difficulty': 'beginner',
                        'time_estimate': 30,
                        'materials': 'Matita HB, carta A4, gomma pane'
                    }
                },
                {
                    'title': 'Proporzioni e Misurazione',
                    'content': '''Impareremo tecniche fondamentali per la misurazione:
                    • Il metodo della matita per misurare proporzioni
                    • La regola dei terzi nella composizione
                    • Come disegnare forme geometriche in proporzione
                    • Esercizi pratici di osservazione
                    
                    Le proporzioni corrette sono la base di ogni disegno realistico.''',
                    'lesson_type': 'practical',
                    'duration': 60,
                    'exercise': {
                        'title': 'Studio delle Proporzioni di Oggetti Semplici',
                        'description': '''Scegli 3 oggetti di casa (es: mela, bottiglia, libro) e:
                        • Disegnali usando il metodo della matita per le proporzioni
                        • Confronta altezza e larghezza
                        • Aggiungi le ombre di base
                        
                        Non preoccuparti dei dettagli, focus sulle proporzioni!''',
                        'exercise_type': 'practical',
                        'difficulty': 'beginner',
                        'time_estimate': 45,
                        'materials': 'Matita HB, carta A4, 3 oggetti da casa'
                    }
                },
                {
                    'title': 'Chiaroscuro: Luci e Ombre',
                    'content': '''Impariamo a dare volume ai nostri disegni:
                    • Come identificare la fonte di luce
                    • Le 5 tipologie di ombre (cast shadow, core shadow, etc.)
                    • Tecniche di sfumatura con la matita
                    • Creazione di volume attraverso il chiaroscuro
                    
                    Il chiaroscuro trasforma un disegno piatto in arte tridimensionale.''',
                    'lesson_type': 'practical',
                    'duration': 75,
                    'exercise': {
                        'title': 'Studio di una Sfera con Chiaroscuro',
                        'description': '''Disegna una sfera perfetta e applica il chiaroscuro:
                        • Identifica la fonte di luce
                        • Aggiungi highlight, mezzi toni, ombre proprie e portate
                        • Sfuma gradualmente da chiaro a scuro
                        • Crea l'ombra proiettata sul piano
                        
                        Questo esercizio è fondamentale per capire il volume!''',
                        'exercise_type': 'technique',
                        'difficulty': 'intermediate',
                        'time_estimate': 60,
                        'materials': 'Matite da H a 4B, carta liscia, tortillon, gomma pane'
                    }
                }
            ]
        },
        {
            'title': 'Pittura ad Acquerello: Tecniche e Creatività',
            'description': '''Scopri la magia dell'acquerello! Un corso dedicato a questa tecnica affascinante 
            che permette di creare opere delicate e luminose. Dalla teoria del colore alle tecniche avanzate.''',
            'category': 'acquerello',
            'lessons': [
                {
                    'title': 'Introduzione all\'Acquerello e Materiali',
                    'content': '''Benvenuti nel mondo dell'acquerello!
                    • Tipi di carta per acquerello (grana e grammatura)
                    • Pennelli: forme, dimensioni e utilizzi
                    • Colori: qualità, pigmenti e trasparenza
                    • Preparazione del tavolo di lavoro
                    
                    L'acquerello richiede pazienza ma regala risultati unici!''',
                    'lesson_type': 'theory',
                    'duration': 40,
                    'exercise': {
                        'title': 'Test dei Materiali e Prime Stesure',
                        'description': '''Familiarizza con i tuoi materiali:
                        • Testa 8 colori diversi su carta asciutta
                        • Prova gli stessi colori su carta bagnata
                        • Esperimenta con diversi pennelli
                        • Crea gradazioni di colore
                        
                        Osserva come i colori si comportano diversamente!''',
                        'exercise_type': 'practical',
                        'difficulty': 'beginner',
                        'time_estimate': 35,
                        'materials': 'Acquerelli base, carta 300g, pennelli tondi n.6 e n.12, acqua, stracci'
                    }
                },
                {
                    'title': 'Tecniche Base: Bagnato su Bagnato e su Asciutto',
                    'content': '''Le due tecniche fondamentali dell'acquerello:
                    • Wet-on-wet: colore su carta bagnata
                    • Wet-on-dry: colore su carta asciutta
                    • Controllo dell'acqua e del timing
                    • Effetti speciali e texture naturali
                    
                    Ogni tecnica ha il suo carattere e utilizzo specifico.''',
                    'lesson_type': 'practical',
                    'duration': 55,
                    'exercise': {
                        'title': 'Paesaggio Semplice con Entrambe le Tecniche',
                        'description': '''Dipingi un semplice paesaggio che include:
                        • Cielo con nuvole (wet-on-wet)
                        • Montagne in lontananza (wet-on-dry)
                        • Lago che riflette il cielo
                        • Alberi in primo piano (wet-on-dry)
                        
                        Focus sulla differenza tra le due tecniche!''',
                        'exercise_type': 'creative',
                        'difficulty': 'intermediate',
                        'time_estimate': 50,
                        'materials': 'Acquerelli, carta 300g, pennelli vari, spugna naturale'
                    }
                }
            ]
        },
        {
            'title': 'Scultura in Argilla: Dalla Forma all\'Espressione',
            'description': '''Un viaggio nel mondo tridimensionale della scultura. Imparerai a modellare l'argilla, 
            creare forme espressive e dare vita alle tue idee attraverso il volume e la texture.''',
            'category': 'scultura',
            'lessons': [
                {
                    'title': 'Introduzione alla Scultura e Preparazione dell\'Argilla',
                    'content': '''Iniziamo il nostro percorso scultoreo:
                    • Tipi di argilla e loro caratteristiche
                    • Preparazione e conservazione dell'argilla
                    • Strumenti base per la scultura
                    • Tecniche di impasto e wedging
                    
                    La scultura ci permette di pensare in tre dimensioni!''',
                    'lesson_type': 'practical',
                    'duration': 50,
                    'exercise': {
                        'title': 'Forme Geometriche di Base',
                        'description': '''Crea le forme fondamentali in argilla:
                        • Un cubo perfetto di 5cm per lato
                        • Una sfera liscia e uniforme
                        • Un cilindro con base e altezza uguali
                        • Un cono con punta centrata
                        
                        Focus sulla precisione delle forme e superficie liscia.''',
                        'exercise_type': 'technique',
                        'difficulty': 'beginner',
                        'time_estimate': 40,
                        'materials': 'Argilla, stecche, spugna, acqua, tavola da lavoro'
                    }
                },
                {
                    'title': 'Tecniche di Modellamento e Texture',
                    'content': '''Sviluppiamo le tecniche espressive:
                    • Addizione e sottrazione di materiale
                    • Creazione di texture con strumenti diversi
                    • Tecniche di lisciatura e rifinitura
                    • Come ottenere superfici diverse
                    
                    La texture aggiunge carattere e interesse visivo alla scultura.''',
                    'lesson_type': 'practical',
                    'duration': 65,
                    'exercise': {
                        'title': 'Ciotola Decorativa con Texture',
                        'description': '''Modella una ciotola funzionale che includa:
                        • Forma armoniosa e proporzioni equilibrate
                        • Almeno 3 tipi di texture diverse sulla superficie
                        • Decorazioni incise o in rilievo
                        • Finitura liscia all'interno
                        
                        Sperimenta con oggetti diversi per creare texture!''',
                        'exercise_type': 'creative',
                        'difficulty': 'intermediate',
                        'time_estimate': 75,
                        'materials': 'Argilla, set di stecche, oggetti texturizzanti, spugna'
                    }
                }
            ]
        }
    ]

    # Crea i corsi con le relative lezioni ed esercizi
    with transaction.atomic():
        for course_data in courses_data:
            # Crea il corso
            course = Course.objects.create(
                title=course_data['title'],
                description=course_data['description'],
                category=course_data['category'],
                teacher=teacher
            )
            print(f"📚 Creato corso: {course.title}")
            
            # Crea le lezioni per questo corso
            for order, lesson_data in enumerate(course_data['lessons'], 1):
                lesson = Lesson.objects.create(
                    title=lesson_data['title'],
                    content=lesson_data['content'],
                    lesson_type=lesson_data['lesson_type'],
                    duration=lesson_data['duration'],
                    course=course,
                    teacher=teacher,
                    order=order
                )
                print(f"  📖 Creata lezione {order}: {lesson.title}")
                
                # Crea l'esercizio per questa lezione
                if 'exercise' in lesson_data:
                    exercise_data = lesson_data['exercise']
                    exercise = Exercise.objects.create(
                        title=exercise_data['title'],
                        description=exercise_data['description'],
                        exercise_type=exercise_data['exercise_type'],
                        difficulty=exercise_data['difficulty'],
                        time_estimate=exercise_data['time_estimate'],
                        materials=exercise_data['materials'],
                        lesson=lesson
                    )
                    print(f"    ✏️ Creato esercizio: {exercise.title}")

    print("\n🎉 Database popolato con successo!")
    print(f"✅ Creati {Course.objects.count()} corsi")
    print(f"✅ Create {Lesson.objects.count()} lezioni")
    print(f"✅ Creati {Exercise.objects.count()} esercizi")
    
    # Mostra riassunto
    print("\n📊 Riassunto corsi creati:")
    for course in Course.objects.all():
        lesson_count = course.lessons_in_course.count()
        exercise_count = sum(lesson.exercises.count() for lesson in course.lessons_in_course.all())
        print(f"• {course.title}")
        print(f"  Lezioni: {lesson_count} | Esercizi: {exercise_count}")

if __name__ == "__main__":
    create_sample_data()
