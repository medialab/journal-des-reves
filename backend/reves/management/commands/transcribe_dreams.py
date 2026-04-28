"""
Script pour traiter la transcription des rêves avec le modèle Whisper
Peut être exécuté comme command Django ou importé comme module
Usage: python manage.py transcribe_dreams 
ou: python manage.py transcribe_dreams --reve-id 123
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from reves.models import Reve
from django.core.management.base import BaseCommand
from django.core.management import CommandError


class TranscriberService:
    """Service pour la transcription des rêves avec Whisper"""
    
    def __init__(self, model_name=None):
        """Initialiser le service Whisper"""
        self.model_name = model_name or os.getenv('WHISPER_MODEL', 'large-v3-turbo')
        self.model = None

        try:
            import whisper
            self.whisper = whisper
            self.model = self.whisper.load_model(self.model_name)
            self.is_loaded = True
            print(f"✅ Modèle Whisper '{self.model_name}' chargé avec succès")
        except ImportError:
            self.is_loaded = False
            print("❌ Le module 'openai-whisper' n'est pas installé")
            print("   Installez-le avec: pip install openai-whisper")
    
    def transcribe(self, audio_file_path):
        """
        Transcrire un fichier audio WAV avec Whisper
        
        Args:
            audio_file_path (str): Chemin absolu du fichier audio
            
        Returns:
            str: Texte transcrit, ou None si erreur
        """
        if not self.is_loaded:
            raise Exception("Whisper n'est pas chargé. Installez openai-whisper.")
        if not self.model:
            raise Exception("Modèle Whisper non initialisé.")
        
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Fichier audio introuvable: {audio_file_path}")
        
        print(f"🎤 Transcription de: {audio_file_path}")
        
        try:
            # Transcrire l'audio
            result = self.model.transcribe(audio_file_path, language="fr")
            
            transcription_text = result.get("text", "").strip()
            
            if not transcription_text:
                raise Exception("Aucun texte transcrit")
            
            print(f"✅ Transcription réussie: {transcription_text[:100]}...")
            return transcription_text
            
        except FileNotFoundError as error:
            if 'ffmpeg' in str(error):
                error_msg = """❌ ffmpeg n'est pas disponible
            
Pour installer ffmpeg:
  - Debian/Ubuntu: sudo apt-get install ffmpeg
  - macOS: brew install ffmpeg
  - Windows: https://ffmpeg.org/download.html
            
Après installation, relancez la commande."""
                print(error_msg)
            else:
                print(f"❌ Erreur fichier: {error}")
            raise
        except Exception as error:
            print(f"❌ Erreur lors de la transcription: {error}")
            raise


def transcribe_reve(reve_id, service=None):
    """
    Transcrire un rêve spécifique
    
    Args:
        reve_id (int): ID du rêve à transcrire
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        reve = Reve.objects.get(id=reve_id)
    except Reve.DoesNotExist:
        print(f"❌ Rêve #{reve_id} introuvable")
        return False
    
    # Passer si déjà transcrit
    if reve.transcription_ready and reve.transcription:
        print(f"⏭️  Rêve #{reve_id} déjà transcrit")
        return True
    
    # Obtenir le chemin du fichier audio
    if not reve.audio:
        print(f"❌ Aucun fichier audio pour le rêve #{reve_id}")
        return False
    
    audio_file_path = reve.audio.path
    
    # Transcrire
    service = service or TranscriberService()
    try:
        transcription = service.transcribe(audio_file_path)
        
        # Sauvegarder la transcription
        reve.transcription = transcription
        reve.transcription_ready = True
        reve.save()
        
        print(f"✅ Rêve #{reve_id} transcrit et sauvegardé")
        return True
        
    except Exception as error:
        print(f"❌ Erreur lors de la transcription du rêve #{reve_id}: {error}")
        reve.transcription = f"Erreur lors de la transcription: {error}"
        reve.transcription_ready = False
        reve.save()
        return False


def transcribe_all_pending(service=None):
    """
    Transcrire tous les rêves en attente de transcription
    
    Returns:
        dict: Statistiques de transcription
    """
    # Trouver les rêves non transcrit
    pending = Reve.objects.filter(transcription_ready=False)
    
    stats = {
        'total': pending.count(),
        'success': 0,
        'failed': 0
    }
    
    if stats['total'] == 0:
        print("✅ Aucune transcription en attente")
        return stats

    service = service or TranscriberService()
    
    print(f"🎤 Transcription de {stats['total']} rêve(s) en attente...")
    
    for reve in pending:
        if transcribe_reve(reve.id, service=service):
            stats['success'] += 1
        else:
            stats['failed'] += 1
    
    print(f"\n📊 Résultats: {stats['success']} réussi(e)s, {stats['failed']} échoué(e)s")
    return stats


class Command(BaseCommand):
    help = 'Transcrire les rêves enregistrés avec le modèle Whisper'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reve-id',
            type=int,
            help='ID spécifique du rêve à transcrire'
        )
        parser.add_argument(
            '--model',
            type=str,
            default=os.getenv('WHISPER_MODEL', 'large-v3-turbo'),
            help='Modèle Whisper local à utiliser (défaut: large-v3-turbo)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Transcrire tous les rêves en attente (défaut)'
        )
    
    def handle(self, *args, **options):
        reve_id = options.get('reve_id')
        all_flag = options.get('all')
        model_name = options.get('model')
        service = TranscriberService(model_name=model_name)

        if not service.is_loaded:
            raise CommandError("Whisper n'est pas disponible. Vérifiez l'installation locale de openai-whisper.")
        
        if reve_id:
            # Transcrire un rêve spécifique
            success = transcribe_reve(reve_id, service=service)
            if not success:
                raise CommandError(f"Impossible de transcrire le rêve #{reve_id}")
        elif all_flag or not reve_id:
            # Transcrire tous les rêves en attente (par défaut)
            stats = transcribe_all_pending(service=service)
            if stats['failed'] > 0:
                raise CommandError(f"{stats['failed']} rêve(s) n'ont pas pu être transcrit(s)")
        
        self.stdout.write(self.style.SUCCESS('✅ Transcription terminée'))


if __name__ == '__main__':
    # Exécution directe du script
    import argparse
    
    parser = argparse.ArgumentParser(description='Transcrire les rêves avec Whisper')
    parser.add_argument('--reve-id', type=int, help='ID spécifique du rêve')
    parser.add_argument('--all', action='store_true', help='Transcrire tous les rêves en attente')
    parser.add_argument('--model', type=str, default=os.getenv('WHISPER_MODEL', 'large-v3-turbo'), help='Modèle Whisper local à utiliser')
    
    args = parser.parse_args()
    
    service = TranscriberService(model_name=args.model)

    if args.reve_id:
        transcribe_reve(args.reve_id, service=service)
    else:
        transcribe_all_pending(service=service)
