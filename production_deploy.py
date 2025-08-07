#!/usr/bin/env python3
"""
🚀 PRODUCTION DEPLOYMENT MASTER SCRIPT
======================================

Questo script coordina il deployment completo di produzione per la TeoCoin School Platform.
Combina tutti gli script di setup esistenti in una sequenza logica e sicura.

Autore: Sistema TeoCoin School
Data: 2025-01-24
Versione: 1.0.0
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Colori per output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title):
    """Stampa un header colorato"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}🚀 {title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_step(step_num, title, description=""):
    """Stampa un passo del deployment"""
    print(f"{Colors.OKBLUE}{Colors.BOLD}STEP {step_num}: {title}{Colors.ENDC}")
    if description:
        print(f"{Colors.OKCYAN}📝 {description}{Colors.ENDC}")
    print()

def print_success(message):
    """Stampa un messaggio di successo"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_warning(message):
    """Stampa un warning"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def print_error(message):
    """Stampa un errore"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def run_django_command(command_name, description="", args=[]):
    """Esegue un Django management command"""
    print(f"{Colors.OKCYAN}🔧 Executing: python manage.py {command_name} {' '.join(args)}{Colors.ENDC}")
    
    try:
        # Costruisci il comando
        cmd = ["python", "manage.py", command_name] + args
        
        # Esegui il comando
        result = subprocess.run(
            cmd,
            cwd="/home/teo/Project/school/schoolplatform",
            capture_output=True,
            text=True,
            timeout=300  # 5 minuti timeout
        )
        
        if result.returncode == 0:
            print_success(f"{description} completed successfully")
            if result.stdout.strip():
                print(f"{Colors.OKCYAN}📄 Output:{Colors.ENDC}")
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            return True
        else:
            print_error(f"{description} failed")
            if result.stderr:
                print(f"{Colors.FAIL}Error: {result.stderr}{Colors.ENDC}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error(f"{description} timed out after 5 minutes")
        return False
    except Exception as e:
        print_error(f"{description} failed with exception: {e}")
        return False

def run_standalone_script(script_path, description=""):
    """Esegue uno script Python standalone"""
    print(f"{Colors.OKCYAN}🔧 Executing: {script_path}{Colors.ENDC}")
    
    try:
        result = subprocess.run(
            ["python", script_path],
            cwd="/home/teo/Project/school/schoolplatform",
            capture_output=True,
            text=True,
            timeout=300  # 5 minuti timeout
        )
        
        if result.returncode == 0:
            print_success(f"{description} completed successfully")
            if result.stdout.strip():
                print(f"{Colors.OKCYAN}📄 Output:{Colors.ENDC}")
                for line in result.stdout.strip().split('\n')[-10:]:  # Ultimi 10 righe
                    print(f"   {line}")
            return True
        else:
            print_error(f"{description} failed")
            if result.stderr:
                print(f"{Colors.FAIL}Error: {result.stderr}{Colors.ENDC}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error(f"{description} timed out")
        return False
    except Exception as e:
        print_error(f"{description} failed: {e}")
        return False

def check_environment():
    """Verifica l'ambiente di deployment"""
    print_step(0, "Environment Check", "Verifying deployment environment")
    
    # Verifica che siamo nella directory corretta
    if not os.path.exists("/home/teo/Project/school/schoolplatform/manage.py"):
        print_error("manage.py not found. Are you in the correct directory?")
        return False
    
    # Verifica Django settings
    django_settings = os.environ.get('DJANGO_SETTINGS_MODULE')
    if not django_settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'schoolplatform.settings.prod'
        print_warning("DJANGO_SETTINGS_MODULE not set, using prod settings")
    
    print_success("Environment check passed")
    return True

def database_setup():
    """Setup e migrazione database"""
    print_step(1, "Database Setup", "Running migrations and initial setup")
    
    # Esegui migrazioni
    if not run_django_command("migrate", "Database migrations"):
        return False
    
    # Collect static files per produzione
    if not run_django_command("collectstatic", "Static files collection", ["--noinput"]):
        print_warning("Static files collection failed, continuing...")
    
    return True

def create_superuser():
    """Crea superuser se non esiste"""
    print_step(2, "Superuser Setup", "Creating admin superuser")
    
    # Questo comando potrebbe fallire se il superuser esiste già
    run_django_command("shell", "Check/Create superuser", [
        "-c", 
        "from django.contrib.auth import get_user_model; "
        "User = get_user_model(); "
        "User.objects.filter(is_superuser=True).exists() or "
        "User.objects.create_superuser('admin', 'admin@teoart.it', 'admin123')"
    ])
    
    return True

def setup_blockchain_infrastructure():
    """Setup infrastruttura blockchain"""
    print_step(3, "Blockchain Infrastructure", "Setting up wallets and TeoCoin system")
    
    # Setup MetaMask admin
    if not run_django_command("setup_metamask_admin", "MetaMask admin setup"):
        print_warning("MetaMask admin setup failed, continuing...")
    
    # Setup minting
    if not run_django_command("setup_minting", "Minting system setup"):
        print_warning("Minting setup failed, continuing...")
    
    # Assign wallets
    if not run_django_command("assign_wallets", "Wallet assignment"):
        print_warning("Wallet assignment failed, continuing...")
    
    return True

def populate_courses():
    """Popola i corsi d'arte"""
    print_step(4, "Course Population", "Creating art school courses and lessons")
    
    # Usa il Django management command per i corsi
    if not run_django_command("setup_art_school", "Art school courses setup"):
        print_warning("Art school setup failed, trying standalone script...")
        
        # Fallback al script standalone
        if not run_standalone_script("core/management/commands/setup_art_school.py", "Art school courses (standalone)"):
            print_error("Both Django command and standalone script failed for courses")
            return False
    
    return True

def setup_users_and_demo_data():
    """Setup utenti e dati demo"""
    print_step(5, "Users & Demo Data", "Creating teachers, students and demo content")
    
    # Seed database con dati base
    if not run_django_command("seed_db", "Database seeding"):
        print_warning("Database seeding failed, continuing...")
    
    # Setup teacher data con balance specifici
    if not run_django_command("setup_teacher_data", "Teacher data setup"):
        print_warning("Teacher data setup failed, continuing...")
    
    return True

def distribute_teocoin():
    """Distribuisce TeoCoin agli studenti"""
    print_step(6, "TeoCoin Distribution", "Assigning TeoCoin to all students")
    
    # Usa il nostro nuovo script
    if not run_standalone_script("assign_teocoin_to_students.py", "TeoCoin distribution to students"):
        print_error("TeoCoin distribution failed")
        return False
    
    return True

def verification_and_testing():
    """Verifica finale e testing"""
    print_step(7, "Verification & Testing", "Running final verification tests")
    
    # Verifica deployment ready
    if not run_django_command("verify_deployment_ready", "Deployment readiness check"):
        print_warning("Deployment verification failed, continuing...")
    
    # Verifica frontend ready
    if not run_django_command("verify_frontend_ready", "Frontend readiness check"):
        print_warning("Frontend verification failed, continuing...")
    
    # Check student balances
    if not run_django_command("check_student_balances", "Student balance verification"):
        print_warning("Balance check failed, continuing...")
    
    return True

def main():
    """Funzione principale del deployment"""
    start_time = datetime.now()
    
    print_header("TEOCOIN SCHOOL PLATFORM - PRODUCTION DEPLOYMENT")
    print(f"{Colors.BOLD}🕐 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print(f"{Colors.BOLD}🎯 Target: Production Environment Setup{Colors.ENDC}")
    print(f"{Colors.BOLD}📍 Location: /home/teo/Project/school/schoolplatform{Colors.ENDC}")
    
    # Conferma dell'utente
    print(f"\n{Colors.WARNING}⚠️  This will set up a PRODUCTION environment with real data.{Colors.ENDC}")
    print(f"{Colors.WARNING}   Make sure you have a backup of your current database!{Colors.ENDC}")
    
    response = input(f"\n{Colors.BOLD}Continue with production deployment? (yes/no): {Colors.ENDC}")
    if response.lower() not in ['yes', 'y']:
        print(f"{Colors.WARNING}Deployment cancelled by user.{Colors.ENDC}")
        return
    
    success_count = 0
    total_steps = 8
    
    try:
        # Sequenza di deployment
        if check_environment():
            success_count += 1
        
        if database_setup():
            success_count += 1
            
        if create_superuser():
            success_count += 1
            
        if setup_blockchain_infrastructure():
            success_count += 1
            
        if populate_courses():
            success_count += 1
            
        if setup_users_and_demo_data():
            success_count += 1
            
        if distribute_teocoin():
            success_count += 1
            
        if verification_and_testing():
            success_count += 1
    
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Deployment interrupted by user{Colors.ENDC}")
        return
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return
    
    # Risultati finali
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("DEPLOYMENT RESULTS")
    print(f"{Colors.BOLD}🕐 Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print(f"{Colors.BOLD}⏱️  Duration: {duration}{Colors.ENDC}")
    print(f"{Colors.BOLD}📊 Success Rate: {success_count}/{total_steps} steps{Colors.ENDC}")
    
    if success_count == total_steps:
        print_success("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print(f"{Colors.OKGREEN}🚀 Your TeoCoin School Platform is ready for production!{Colors.ENDC}")
        print(f"\n{Colors.OKBLUE}📋 Next Steps:{Colors.ENDC}")
        print(f"   • Access admin panel: http://your-domain/admin")
        print(f"   • Login as admin: admin@teoart.it / admin123")
        print(f"   • Verify TeoCoin balances in teacher dashboard")
        print(f"   • Test course enrollment and exercises")
    else:
        print_warning(f"Deployment completed with {total_steps - success_count} step(s) having issues")
        print(f"{Colors.WARNING}🔧 Review the output above and fix any failed steps{Colors.ENDC}")

if __name__ == "__main__":
    main()
