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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

from polls.models import Reve
from django.core.management.base import BaseCommand
from django.core.management import CommandError


class TranscriberService:
    """Service pour la transcription des rêves avec Whisper"""
    
    def __init__(self):
        """Initialiser le service Whisper"""
        try:
            import whisper
            self.whisper = whisper
            self.is_loaded = True
            print("✅ Modèle Whisper chargé avec succès")
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
        
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Fichier audio introuvable: {audio_file_path}")
        
        print(f"🎤 Transcription de: {audio_file_path}")
        
        try:
            # Charger le modèle Whisper (tiny pour plus de rapidité)
            # Options: tiny, base, small, medium, large
            model = self.whisper.load_model("base")
            
            # Transcrire l'audio
            result = model.transcribe(audio_file_path, language="fr")
            
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


def transcribe_reve(reve_id):
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
    service = TranscriberService()
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


def transcribe_all_pending():
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
    
    print(f"🎤 Transcription de {stats['total']} rêve(s) en attente...")
    
    for reve in pending:
        if transcribe_reve(reve.id):
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
            '--all',
            action='store_true',
            help='Transcrire tous les rêves en attente (défaut)'
        )
    
    def handle(self, *args, **options):
        reve_id = options.get('reve_id')
        all_flag = options.get('all')
        
        if reve_id:
            # Transcrire un rêve spécifique
            success = transcribe_reve(reve_id)
            if not success:
                raise CommandError(f"Impossible de transcrire le rêve #{reve_id}")
        elif all_flag or not reve_id:
            # Transcrire tous les rêves en attente (par défaut)
            stats = transcribe_all_pending()
            if stats['failed'] > 0:
                raise CommandError(f"{stats['failed']} rêve(s) n'ont pas pu être transcrit(s)")
        
        self.stdout.write(self.style.SUCCESS('✅ Transcription terminée'))


if __name__ == '__main__':
    # Exécution directe du script
    import argparse
    
    parser = argparse.ArgumentParser(description='Transcrire les rêves avec Whisper')
    parser.add_argument('--reve-id', type=int, help='ID spécifique du rêve')
    parser.add_argument('--all', action='store_true', help='Transcrire tous les rêves en attente')
    
    args = parser.parse_args()
    
    if args.reve_id:
        transcribe_reve(args.reve_id)
    else:
        transcribe_all_pending()
