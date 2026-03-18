"""
EXEMPLE d'intégration avec APScheduler pour les tâches planifiées en background
Ce fichier est un exemple - pour l'utiliser, installez django-apscheduler:
    pip install django-apscheduler

Intégration dans polls/apps.py
"""

# ============================================
# Option 1 : Utiliser APScheduler (Simplifié)
# ============================================

"""
# Dans polls/apps.py, remplacez le contenu par:

from django.apps import AppConfig
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

logger = logging.getLogger(__name__)

class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'
    
    def ready(self):
        '''Initialiser le scheduler au démarrage de l'app'''
        try:
            # Créer un scheduler en background
            scheduler = BackgroundScheduler(daemon=True)
            
            # Ajouter le job pour les rappels quotidiens (8h du matin)
            scheduler.add_job(
                func=lambda: call_command('send_daily_reminder'),
                trigger='cron',
                hour=8,
                minute=0,
                id='send_daily_reminder',
                replace_existing=True
            )
            
            # Ajouter le job pour les rappels questionnaire (10h)
            scheduler.add_job(
                func=lambda: call_command('send_questionnaire_reminder'),
                trigger='cron',
                hour=10,
                minute=0,
                id='send_questionnaire_reminder',
                replace_existing=True
            )
            
            # Démarrer le scheduler
            scheduler.start()
            logger.info('✅ APScheduler started - Tasks scheduled!')
            
        except Exception as e:
            logger.error(f'❌ APScheduler error: {e}')
"""

# ============================================
# Option 2 : Utiliser Celery + Celery Beat
# ============================================

"""
Installation:
    pip install celery django-celery-beat django-celery-results

Configuration dans settings.py:
    INSTALLED_APPS = [
        ...
        'django_celery_beat',
        'django_celery_results',
    ]
    
    CELERY_BROKER_URL = 'redis://localhost:6379'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'

    CELERY_BEAT_SCHEDULE = {
        'send_daily_reminder': {
            'task': 'polls.tasks.send_daily_reminder_task',
            'schedule': crontab(hour=8, minute=0),  # 8h du matin
        },
        'send_questionnaire_reminder': {
            'task': 'polls.tasks.send_questionnaire_reminder_task',
            'schedule': crontab(hour=10, minute=0),  # 10h
        },
    }

Créer polls/tasks.py:

    from celery import shared_task
    from django.core.management import call_command
    import logging
    
    logger = logging.getLogger(__name__)
    
    @shared_task
    def send_daily_reminder_task():
        try:
            call_command('send_daily_reminder')
            logger.info('✅ Daily reminders sent')
        except Exception as e:
            logger.error(f'❌ Error: {e}')
    
    @shared_task
    def send_questionnaire_reminder_task():
        try:
            call_command('send_questionnaire_reminder')
            logger.info('✅ Questionnaire reminders sent')
        except Exception as e:
            logger.error(f'❌ Error: {e}')

Lancer:
    celery -A mysite worker -l info
    celery -A mysite beat -l info
"""

# ============================================
# Option 3 : Script Linux/System personnalisé
# ============================================

"""
Créer /usr/local/bin/reves_notifications.sh:

#!/bin/bash
cd /home/maudyaiche/dev/site_reves/djangotutorial
/usr/bin/python3 manage.py send_daily_reminder >> /var/log/reves_daily.log 2>&1
/usr/bin/python3 manage.py send_questionnaire_reminder >> /var/log/reves_questionnaire.log 2>&1

chmod +x /usr/local/bin/reves_notifications.sh

Puis dans crontab:
0 8 * * * /usr/local/bin/reves_notifications.sh
0 10 * * * /usr/local/bin/reves_notifications.sh
"""

# ============================================
# Option 4 : Supervisor (Production)
# ============================================

"""
Installation:
    sudo apt-get install supervisor

Créer /etc/supervisor/conf.d/reves_scheduler.conf:

[program:reves_notification_worker]
command=bash -c 'while true; do /usr/bin/python3 /home/maudyaiche/dev/site_reves/djangotutorial/manage.py send_daily_reminder && sleep 300; done'
directory=/home/maudyaiche/dev/site_reves/djangotutorial
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/reves_notifications.log

Contrôler:
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl status
"""

# ============================================
# EXEMPLE DE TEST
# ============================================

"""
Pour tester les commandes manuellement:

python3 manage.py send_daily_reminder
python3 manage.py send_questionnaire_reminder

Ou via Django shell:

python3 manage.py shell

from django.core.management import call_command
call_command('send_daily_reminder')
call_command('send_questionnaire_reminder')

# Et vérifier:
from polls.models import Notification
Notification.objects.all().count()
"""

# ============================================
# EXEMPLE COMPLET : using APScheduler
# ============================================

EXAMPLE_POLLS_APPS = """
# polls/apps.py

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'
    scheduler_started = False
    
    def ready(self):
        '''Appelé au démarrage de Django'''
        from apscheduler.schedulers.background import BackgroundScheduler
        from django.core.management import call_command
        
        # Éviter de démarrer plusieurs fois
        if PollsConfig.scheduler_started:
            return
        
        try:
            # Créer le scheduler
            scheduler = BackgroundScheduler({
                'apscheduler.jobstores.default': {
                    'type': 'memory'
                },
                'apscheduler.executors.default': {
                    'class': 'apscheduler.executors.debug.DebugExecutor'
                }
            }, daemon=True)
            
            # Ajouter les jobs
            scheduler.add_job(
                func=lambda: call_command('send_daily_reminder'),
                trigger='cron',
                hour=8,
                minute=0,
                second=0,
                id='daily_reminder',
            )
            
            scheduler.add_job(
                func=lambda: call_command('send_questionnaire_reminder'),
                trigger='cron',
                hour=10,
                minute=0,
                second=0,
                id='questionnaire_reminder',
            )
            
            # Démarrer
            scheduler.start()
            PollsConfig.scheduler_started = True
            logger.info('✅ Notification scheduler started')
            
        except Exception as e:
            logger.error(f'❌ Scheduler error: {e}')
"""

print(EXAMPLE_POLLS_APPS)
