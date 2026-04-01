"""
Service de transcription automatique des rêves
Gère le lancement asynchrone des transcriptions via threading
"""

import threading
import logging
from django.core.management import call_command
from django.core.management.base import CommandError

# Logger configuré centralement via settings.LOGGING
logger = logging.getLogger('transcription')


class TranscriptionThread(threading.Thread):
    """Thread worker pour transcrire un rêve de manière asynchrone"""
    
    def __init__(self, reve_id):
        super().__init__(daemon=True)
        self.reve_id = reve_id
        self.name = f"TranscriptionThread-{reve_id}"
    
    def run(self):
        """Exécuter la transcription du rêve"""
        try:
            logger.info(f"🎤 Démarrage de la transcription du rêve #{self.reve_id}")
            
            # Appeler la commande Django de transcription
            call_command(
                'transcribe_dreams',
                reve_id=self.reve_id,
                verbosity=2
            )
            
            logger.info(f"✅ Transcription du rêve #{self.reve_id} terminée")
            
        except CommandError as e:
            logger.error(f"❌ Erreur de commande pour rêve #{self.reve_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la transcription du rêve #{self.reve_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())


def start_transcription_async(reve_id):
    """
    Lancer la transcription d'un rêve de manière asynchrone (non-bloquante)
    
    Args:
        reve_id (int): ID du rêve à transcrire
        
    Returns:
        bool: True si le thread a bien démarré
    """
    try:
        logger.info(f"📝 Création du thread de transcription pour rêve #{reve_id}")
        
        # Créer et lancer le thread
        thread = TranscriptionThread(reve_id)
        thread.start()
        
        logger.info(f"🚀 Thread de transcription lancé pour rêve #{reve_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du lancement du thread: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
