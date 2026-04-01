"""
Page de test pour tester le script de transcription des rêves
Permet de tester l'envoi d'audio pour transcription et de corrections si besoin
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

from django.core.management.base import BaseCommand
from reves.management.commands.transcribe_dreams import TranscriberService
from reves.models import Reve
import json


class Command(BaseCommand):
    help = 'Test the Whisper transcription service for dreams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reve-id',
            type=int,
            help='ID du rêve à transcrire'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lister tous les rêves en attente de transcription'
        )
        parser.add_argument(
            '--test-file',
            type=str,
            help='Chemin vers un fichier audio pour testing'
        )

    def handle(self, *args, **options):
        """Handler principal"""
        
        self.stdout.write(
            self.style.SUCCESS('\n' + '='*70)
        )
        self.stdout.write(
            self.style.SUCCESS('🎤 TEST DU SERVICE DE TRANSCRIPTION WHISPER')
        )
        self.stdout.write(
            self.style.SUCCESS('='*70 + '\n')
        )

        # Initialiser le service
        service = TranscriberService()
        
        if not service.is_loaded:
            self.stdout.write(
                self.style.ERROR(
                    '❌ ERREUR: Le module Whisper n\'est pas installé\n'
                    'Installez-le avec: pip install openai-whisper\n'
                )
            )
            return

        # Test 1: Lister les rêves en attente
        if options['list']:
            self._list_pending_dreams()
            return

        # Test 2: Transcrire un rêve spécifique
        if options['reve_id']:
            self._transcribe_reve(service, options['reve_id'])
            return

        # Test 3: Tester avec un fichier audio spécifique
        if options['test_file']:
            self._test_transcribe_file(service, options['test_file'])
            return

        # Par défaut: Afficher le status
        self._show_status(service)

    def _show_status(self, service):
        """Afficher le status du service"""
        self.stdout.write(
            self.style.SUCCESS('✓ Service Whisper chargé et prêt')
        )
        self.stdout.write('\nCommandes de test disponibles:\n')
        self.stdout.write(
            self.style.WARNING('  python manage.py test_transcribe --list')
        )
        self.stdout.write('    → Lister tous les rêves en attente de transcription\n')
        
        self.stdout.write(
            self.style.WARNING('  python manage.py test_transcribe --reve-id 123')
        )
        self.stdout.write('    → Transcrire un rêve spécifique\n')
        
        self.stdout.write(
            self.style.WARNING('  python manage.py test_transcribe --test-file /path/to/audio.wav')
        )
        self.stdout.write('    → Tester avec un fichier audio\n')

        # Afficher les rêves en attente
        self._list_pending_dreams()

    def _list_pending_dreams(self):
        """Lister les rêves en attente de transcription"""
        pending = Reve.objects.filter(transcription_ready=False, audio__isnull=False)
        
        if not pending.exists():
            self.stdout.write(
                self.style.SUCCESS('✓ Aucun rêve en attente de transcription\n')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'\n📋 {pending.count()} rêvers en attente de transcription:\n')
        )
        
        for reve in pending:
            self.stdout.write(
                f'  ID: {reve.id} | Utilisateur: {reve.profil.user.username} | '
                f'Date: {reve.date} | Audio: {reve.audio.name}'
            )
        
        self.stdout.write()

    def _transcribe_reve(self, service, reve_id):
        """Transcrire un rêve spécifique"""
        try:
            reve = Reve.objects.get(id=reve_id)
        except Reve.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Rêve avec ID {reve_id} non trouvé\n')
            )
            return

        if not reve.audio:
            self.stdout.write(
                self.style.ERROR('❌ Ce rêve n\'a pas de fichier audio\n')
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f'\n🎤 Transcription du rêve ID {reve_id}...\n'
                f'   Utilisateur: {reve.profil.user.username}\n'
                f'   Date: {reve.date}\n'
                f'   Audio: {reve.audio.name}\n'
            )
        )

        # Obtenir le chemin complet du fichier audio
        audio_path = reve.audio.path

        if not os.path.exists(audio_path):
            self.stdout.write(
                self.style.ERROR(f'❌ Fichier audio non trouvé: {audio_path}\n')
            )
            return

        # Transcrire
        transcription = service.transcribe(audio_path)

        if transcription:
            reve.transcription = transcription
            reve.transcription_ready = True
            reve.save()

            self.stdout.write(
                self.style.SUCCESS('\n✓ Transcription réussie!\n')
            )
            self.stdout.write(
                self.style.SUCCESS(f'Texte (premiers 500 caractères):\n')
            )
            self.stdout.write(
                f'{transcription[:500]}...\n' if len(transcription) > 500 
                else f'{transcription}\n'
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Erreur lors de la transcription\n')
            )

    def _test_transcribe_file(self, service, file_path):
        """Tester la transcription avec un fichier spécifique"""
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'❌ Fichier non trouvé: {file_path}\n')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'\n🎤 Test de transcription avec: {file_path}\n')
        )

        transcription = service.transcribe(file_path)

        if transcription:
            self.stdout.write(
                self.style.SUCCESS('\n✓ Transcription réussie!\n')
            )
            self.stdout.write('Texte transcrit:\n')
            self.stdout.write(f'{transcription}\n')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Erreur lors de la transcription\n')
            )
