"""
Tests PostgreSQL - Ultra léger pour éviter bugs VS Code

Exécution:
  cd backend && DJANGO_ENV_FILE=../.env.test python manage.py test tests.test_postgresql_light -v 2
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time, date
from reves.models import Profil, Questionnaire, Reve


class PostgreSQLBasicsTest(TestCase):
    """Tests basiques PostgreSQL"""

    def test_01_database_connection(self):
        """✓ Vérifier connexion PostgreSQL"""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_02_timezone_config(self):
        """✓ Vérifier config timezone Django"""
        from django.conf import settings
        
        self.assertEqual(settings.TIME_ZONE, 'Europe/Paris')
        self.assertTrue(settings.USE_TZ)


class QuestionnaireBasicTest(TestCase):
    """Test basique Questionnaire PostgreSQL"""
    
    fixtures = []  # Pas de fixtures, tout créé dans le test
    
    def test_create_questionnaire_minimal(self):
        """✓ Créer questionnaire minimal"""
        # Créer utilisateur et profil directement en une ligne
        user = User.objects.create_user('test_user')
        profil, _ = Profil.objects.get_or_create(user=user)
        
        # Créer questionnaire (seulement profil est obligatoire)
        q = Questionnaire.objects.create(
            profil=profil,
        )
        
        # Vérifier
        self.assertIsNotNone(q.pk)
        self.assertEqual(q.profil.user.username, 'test_user')

    def test_retrieve_questionnaire(self):
        """✓ Relire questionnaire de la BD"""
        # Setup
        user = User.objects.create_user('test_user_retrieve')
        profil, _ = Profil.objects.get_or_create(user=user)
        
        q = Questionnaire.objects.create(
            profil=profil,
            heure_coucher=time(23, 30),
            heure_reveil=time(7, 30),
            besoin_som=time(8, 0),
        )
        
        # Relire
        q_fetched = Questionnaire.objects.get(pk=q.pk)
        self.assertEqual(str(q_fetched.heure_coucher), '23:30:00')


class ReveBasicTest(TestCase):
    """Test basique Rêve PostgreSQL"""
    
    fixtures = []  # Pas de fixtures
    
    def test_create_reve_minimal(self):
        """✓ Créer rêve minimal"""
        # Setup
        user = User.objects.create_user('test_reve_user')
        profil, _ = Profil.objects.get_or_create(user=user)
        
        # Créer rêve (champs réels du modèle)
        reve = Reve.objects.create(
            profil=profil,
            existence_souvenir=True,
            type_reve=Reve.TypeReve.POSITIF,
        )
        
        # Vérifier
        self.assertIsNotNone(reve.pk)
        self.assertTrue(reve.existence_souvenir)

    def test_reve_datetime_utc(self):
        """✓ Vérifier que created_at est en UTC"""
        # Setup
        user = User.objects.create_user('test_reve_tz')
        profil, _ = Profil.objects.get_or_create(user=user)
        
        reve = Reve.objects.create(
            profil=profil,
            existence_souvenir=True,
        )
        
        # Vérifier
        self.assertIsNotNone(reve.created_at.tzinfo)
        
        # Vérifier conversion locale
        local_time = timezone.localtime(reve.created_at)
        self.assertIsNotNone(local_time.tzinfo)

    def test_retrieve_reve(self):
        """✓ Relire rêve de la BD"""
        # Setup
        user = User.objects.create_user('test_reve_retrieve')
        profil, _ = Profil.objects.get_or_create(user=user)
        
        reve = Reve.objects.create(
            profil=profil,
            existence_souvenir=False,
            type_reve=Reve.TypeReve.NEUTRE,
        )
        
        # Relire
        reve_fetched = Reve.objects.get(pk=reve.pk)
        self.assertEqual(reve_fetched.existence_souvenir, False)
        self.assertEqual(reve_fetched.type_reve, Reve.TypeReve.NEUTRE)


class PostgreSQL_IntegrationTest(TestCase):
    """Test d'intégration Questionnaire + Rêve"""
    
    fixtures = []
    
    def test_questionnaire_and_reve_same_user(self):
        """✓ Questionnaire et Rêve pour même utilisateur"""
        # Setup
        user = User.objects.create_user('test_integration')
        profil, _ = Profil.objects.get_or_create(user=user)
        
        # Créer questionnaire
        q = Questionnaire.objects.create(
            profil=profil,
            heure_coucher=time(23, 30),
            heure_reveil=time(7, 30),
        )
        
        # Créer rêve
        reve = Reve.objects.create(
            profil=profil,
            existence_souvenir=True,
            type_reve=Reve.TypeReve.TRES_POSITIF,
        )
        
        # Vérifier les deux existent et appartiennent au même profil
        q_check = Questionnaire.objects.get(pk=q.pk)
        r_check = Reve.objects.get(pk=reve.pk)
        
        self.assertEqual(q_check.profil.pk, profil.pk)
        self.assertEqual(r_check.profil.pk, profil.pk)
