from django.core.management.base import BaseCommand
from django.db import transaction
from courses.models import Course
from users.models import User


class Command(BaseCommand):
    help = 'Setup art school categories and sample courses'

    def handle(self, *args, **options):
        self.stdout.write("🎨 SETUP SCUOLA D'ARTE - Aggiornamento Categorie e Corsi")
        self.stdout.write("=" * 60)
        
        try:
            # Aggiorna categorie esistenti
            self.update_art_categories()
            
            # Crea corsi di esempio
            self.create_sample_art_courses()
            
            self.stdout.write(self.style.SUCCESS("\n✅ Setup completato con successo!"))
            self.show_courses_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Errore durante il setup: {e}"))
            import traceback
            traceback.print_exc()

    def update_art_categories(self):
        """Aggiorna le categorie dei corsi esistenti con categorie artistiche"""
        
        # Mappatura delle vecchie categorie alle nuove categorie artistiche
        category_mapping = {
            'design': 'design-grafico',
            'creative': 'arte-digitale',
            'web3': 'arte-digitale',
            'programming': 'arte-digitale',
            'other': 'other'
        }
        
        self.stdout.write("🎨 Aggiornamento categorie corsi esistenti...")
        
        with transaction.atomic():
            courses = Course.objects.all()
            updated_count = 0
            
            for course in courses:
                old_category = course.category
                new_category = category_mapping.get(old_category, 'other')
                
                if old_category != new_category:
                    course.category = new_category
                    course.save()
                    updated_count += 1
                    self.stdout.write(f"   ✓ Corso '{course.title}': {old_category} → {new_category}")
            
            self.stdout.write(f"📊 Aggiornati {updated_count} corsi su {courses.count()}")

    def create_sample_art_courses(self):
        """Crea corsi d'arte di esempio"""
        
        self.stdout.write("\n🎭 Creazione corsi d'arte di esempio...")
        
        # Trova un teacher approvato o crea un teacher di esempio
        try:
            teacher = User.objects.filter(role='teacher', is_approved=True).first()
            if not teacher:
                teacher = User.objects.filter(role='teacher').first()
                if teacher:
                    teacher.is_approved = True
                    teacher.save()
                else:
                    # Crea un teacher di esempio
                    teacher = User.objects.create_user(
                        username='maestro_arte',
                        email='maestro@arte.com',
                        password='password123',
                        role='teacher',
                        is_approved=True
                    )
                    self.stdout.write("   ✓ Creato teacher di esempio: maestro_arte")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Errore nella creazione del teacher: {e}"))
            return

        # Corsi d'arte di esempio
        sample_courses = [
            {
                'title': 'Disegno a Matita - Livello Base',
                'description': 'Impara le tecniche fondamentali del disegno a matita, dalla gestione del tratto alle proporzioni. Perfetto per principianti che vogliono iniziare il loro percorso artistico.',
                'category': 'disegno',
                'price': 50
            },
            {
                'title': 'Pittura ad Olio - Tecniche Classiche',
                'description': 'Scopri i segreti della pittura ad olio utilizzando tecniche tramandati dai grandi maestri. Imparerai miscelazione colori, velature e impasto.',
                'category': 'pittura-olio',
                'price': 120
            },
            {
                'title': 'Acquerello per Principianti',
                'description': 'Corso introduttivo all\'acquerello. Imparerai le tecniche base: lavaggi, sfumature, bagnato su bagnato e controllo dell\'acqua.',
                'category': 'acquerello',
                'price': 80
            },
            {
                'title': 'Scultura in Argilla - Workshop Intensivo',
                'description': 'Workshop pratico di scultura in argilla. Dalla preparazione del materiale alla cottura finale. Include tecniche di modellato e decorazione.',
                'category': 'scultura',
                'price': 150
            },
            {
                'title': 'Storia dell\'Arte Rinascimentale',
                'description': 'Viaggio attraverso il Rinascimento italiano. Analizzeremo opere di Leonardo, Michelangelo, Raffaello e le tecniche rivoluzionarie dell\'epoca.',
                'category': 'storia-arte',
                'price': 60
            },
            {
                'title': 'Illustrazione Digitale con Photoshop',
                'description': 'Crea illustrazioni professionali utilizzando Photoshop. Dal concept iniziale alla finalizzazione, perfetto per aspiranti illustratori.',
                'category': 'arte-digitale',
                'price': 90
            },
            {
                'title': 'Fotografia Artistica - Composizione e Luce',
                'description': 'Impara a creare fotografie artistiche memorabili. Focus su composizione, uso della luce naturale e post-produzione creativa.',
                'category': 'fotografia',
                'price': 70
            },
            {
                'title': 'Ceramica Tradizionale - Tornio e Decorazione',
                'description': 'Corso completo di ceramica: uso del tornio, tecniche di modellato, ingobbi, smalti e cottura. Include progetto finale personalizzato.',
                'category': 'ceramica',
                'price': 130
            }
        ]
        
        created_count = 0
        with transaction.atomic():
            for course_data in sample_courses:
                # Controlla se il corso esiste già
                if not Course.objects.filter(title=course_data['title']).exists():
                    course = Course.objects.create(
                        title=course_data['title'],
                        description=course_data['description'],
                        category=course_data['category'],
                        price=course_data['price'],
                        teacher=teacher,
                        is_approved=True  # Pre-approva i corsi di esempio
                    )
                    created_count += 1
                    self.stdout.write(f"   ✓ Creato corso: {course.title} ({course.get_category_display()})")
                else:
                    self.stdout.write(f"   - Corso già esistente: {course_data['title']}")
        
        self.stdout.write(f"📊 Creati {created_count} nuovi corsi d'arte")

    def show_courses_summary(self):
        """Mostra un riepilogo dei corsi disponibili"""
        self.stdout.write("\n📚 Riepilogo corsi disponibili:")
        
        courses_by_category = {}
        for course in Course.objects.filter(is_approved=True):
            category = course.get_category_display()
            if category not in courses_by_category:
                courses_by_category[category] = 0
            courses_by_category[category] += 1
        
        for category, count in sorted(courses_by_category.items()):
            self.stdout.write(f"   {category}: {count} corso{'i' if count > 1 else ''}")
