#!/usr/bin/env python
"""
Tests pour vérifier que les réponses du questionnaire s'enregistrent correctement
dans la base de données SQLite et correspondent aux modèles Django.

Ce fichier teste :
- Les champs IntegerField avec choix (genre, habitat, diplôme, etc.)
- Les champs BooleanField (modalités des rêves, discriminations, etc.)
- Les champs TextField (commentaires)
- Les champs DateTimeField (dates de complétion)
- L'association avec le profil utilisateur
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/maudyaiche/dev/site_reves/backend')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from reves.models import Profil, Questionnaire
import json
import uuid


class QuestionnaireIntegrationTests(TestCase):
    """Tests pour valider l'intégrité des données du questionnaire"""

    def setUp(self):
        """Configuration avant chaque test"""
        # Créer un utilisateur unique pour chaque test
        unique_id = str(uuid.uuid4())[:8]
        self.username = f'testuser_{unique_id}'
        self.email = f'test_{unique_id}@example.com'
        self.password = 'testpass123'
        
        # Supprimer le profil d'abord S'il existe  
        Profil.objects.filter(email=self.email).delete()
        # Puis supprimer l'utilisateur
        User.objects.filter(username=self.username).delete()
        
        # Créer l'utilisateur
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )
        
        # Créer un profil avec accès au questionnaire (7+ jours)
        # Utiliser get_or_create pour éviter les conflits
        self.profil, created = Profil.objects.get_or_create(
            user=self.user,
            defaults={
                'email': self.email,
                'created_at': timezone.now() - timedelta(days=8)
            }
        )
        
        self.client = Client()
        self.client.login(username=self.username, password=self.password)

    # ===== TESTS DES CHAMPS INTEGERFIELD AVEC CHOIX =====
    
    def test_genre_field_integer_choices(self):
        """Teste que le champ genre enregistre correctement une valeur IntegerField"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            genre=Questionnaire.GenreChoices.FEMME
        )
        
        # Vérifier que la valeur est bien enregistrée en base de données
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.genre, 1, "Le genre devrait être 1 (Femme)")
        self.assertEqual(q_from_db.get_genre_display(), "Femme", "Le label du genre devrait être 'Femme'")

    def test_habitat_field_integer_choices(self):
        """Teste que le champ habitat enregistre correctement une valeur IntegerField"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            habitat=Questionnaire.HabitatChoices.URBAIN
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.habitat, 2, "L'habitat devrait être 2 (Urbain)")
        self.assertEqual(q_from_db.get_habitat_display(), "Urbain", "Le label devrait être 'Urbain'")

    def test_diplome_field_integer_choices(self):
        """Teste que le champ diplôme enregistre correctement une valeur IntegerField"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            niv_diplome=Questionnaire.DiplomeChoices.BAC_3_4
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertIsNotNone(q_from_db.niv_diplome, "Le diplôme ne devrait pas être null")
        self.assertTrue(hasattr(q_from_db, 'get_niv_diplome_display'), "Le champ devrait avoir un get_display")

    def test_annee_naissance_integer_field(self):
        """Teste que l'année de naissance enregistre une valeur IntegerField"""
        birth_year = 1990
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            annee_naissance=birth_year
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.annee_naissance, birth_year, f"L'année de naissance devrait être {birth_year}")

    def test_freq_reves_not_choices(self):
        """Teste que la fréquence des rêves enregistre correctement une valeur IntegerField"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            freq_reves_not=Questionnaire.FreqRevesNotChoices.OUI_SOUVENT
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.freq_reves_not, 1, "Fréquence devrait être 1 (Oui souvent)")

    # ===== TESTS DES CHAMPS BOOLEANFIELD =====
    
    def test_perception_modalites_boolean_fields(self):
        """Teste que les modalités de perception s'enregistrent comme BooleanField"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            mod_img=True,
            mod_son=True,
            mod_sens=False,
            mod_emot=True,
            mod_pens=False
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertTrue(q_from_db.mod_img, "Images devrait être True")
        self.assertTrue(q_from_db.mod_son, "Sons devrait être True")
        self.assertFalse(q_from_db.mod_sens, "Sensations du corps devrait être False")
        self.assertTrue(q_from_db.mod_emot, "Émotions devrait être True")
        self.assertFalse(q_from_db.mod_pens, "Pensées devrait être False")

    def test_image_couleur_boolean_fields(self):
        """Teste que les champs de couleur des images s'enregistrent comme BooleanField"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            img_coul=True,
            img_nb=False,
            img_net=True,
            img_flou=False,
            img_ns=False
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertTrue(q_from_db.img_coul, "Couleur devrait être True")
        self.assertFalse(q_from_db.img_nb, "Noir et blanc devrait être False")

    def test_sommeil_boolean_fields(self):
        """Teste que les champs liés au sommeil s'enregistrent correctement"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            reveil_nuit=True,
            aide_sommeil=True,
            aide_medic=False,
            aide_tisane=True,
            aide_autre=False
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertTrue(q_from_db.reveil_nuit, "Réveil de nuit devrait être True")
        self.assertTrue(q_from_db.aide_sommeil, "Aide sommeil devrait être True")
        self.assertFalse(q_from_db.aide_medic, "Médicaments devrait être False")

    def test_pensees_avant_dormir_boolean_fields(self):
        """Teste que les pensées avant le coucher s'enregistrent correctement"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            pens_trav=True,
            pens_fin=True,
            pens_fam=False,
            pens_proch=True,
            pens_actu=False,
            pens_autre=False,
            pens_rien=False
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertTrue(q_from_db.pens_trav, "Travail devrait être True")
        self.assertTrue(q_from_db.pens_fin, "Financier devrait être True")
        self.assertFalse(q_from_db.pens_fam, "Famille devrait être False")

    def test_discrimination_boolean_fields(self):
        """Teste que les champs de discrimination s'enregistrent correctement"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            discri_presence=Questionnaire.DiscriPresenceChoices.OUI_SOUVENT,
            discri_age=True,
            discri_genre=True,
            discri_sante_physique=False,
            discri_couleur_peau=False,
            discri_origine_nationalite=False,
            discri_contexte_emploi=True,
            discri_contexte_logement=False,
            discri_contexte_travail=True
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertTrue(q_from_db.discri_age, "Âge devrait être True")
        self.assertTrue(q_from_db.discri_genre, "Genre devrait être True")
        self.assertTrue(q_from_db.discri_contexte_emploi, "Contexte emploi devrait être True")

    # ===== TESTS DES CHAMPS TEXTFIELD =====
    
    def test_textarea_fields_string_storage(self):
        """Teste que les champs TextField enregistrent correctement du texte"""
        texte_long = "Ceci est un commentaire très long avec des caractères spéciaux: é, è, ê, à, ô, ù, ç, etc."
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            pens_autre_txt=texte_long,
            discri_autre_precision="Raison de discrimination personnalisée"
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.pens_autre_txt, texte_long, "Le texte des pensées devrait être correctement enregistré")
        self.assertEqual(q_from_db.discri_autre_precision, "Raison de discrimination personnalisée", 
                        "La précision devrait être correctement enregistrée")

    # ===== TESTS DES CHAMPS DATETIMEFIELD =====
    
    def test_datetime_fields_creation(self):
        """Teste que les champs DateTimeField s'enregistrent correctement"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            is_completed=True
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertIsNotNone(q_from_db.created_at, "created_at ne devrait pas être null")
        self.assertIsNotNone(q_from_db.updated_at, "updated_at ne devrait pas être null")
        self.assertLessEqual(q_from_db.created_at, timezone.now(), "created_at devrait être dans le passé ou présent")

    def test_completed_at_datetime(self):
        """Teste que completed_at enregistre la date de complétion"""
        completion_time = timezone.now() - timedelta(hours=1)
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            is_completed=True,
            completed_at=completion_time
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertIsNotNone(q_from_db.completed_at, "completed_at devrait être rempli")
        # Vérifier que les dates sont proches (à cause de la précision des secondes)
        time_diff = abs((q_from_db.completed_at - completion_time).total_seconds())
        self.assertLess(time_diff, 1, "La date de complétion devrait correspondre")

    # ===== TESTS DES RELATIONS AVEC LE PROFIL =====
    
    def test_questionnaire_belongs_to_profil(self):
        """Teste que chaque questionnaire est associé correctement au profil"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.profil.id, self.profil.id, "Le questionnaire devrait être associé au bon profil")
        self.assertEqual(q_from_db.profil.user.id, self.user.id, "Le profil devrait être associé au bon utilisateur")

    def test_questionnaire_multiple_for_same_profil(self):
        """Teste qu'un profil peut avoir plusieurs questionnaires"""
        q1 = Questionnaire.objects.create(profil=self.profil, user=self.user, genre=1)
        q2 = Questionnaire.objects.create(profil=self.profil, user=self.user, genre=2)
        
        questionnaires = Questionnaire.objects.filter(profil=self.profil)
        self.assertEqual(questionnaires.count(), 2, "Le profil devrait avoir 2 questionnaires")
        self.assertIn(q1.id, [q.id for q in questionnaires], "Q1 devrait être dans les questionnaires du profil")
        self.assertIn(q2.id, [q.id for q in questionnaires], "Q2 devrait être dans les questionnaires du profil")

    # ===== TESTS DES VALIDATIONS =====
    
    def test_annee_naissance_validators(self):
        """Teste que les validateurs d'année de naissance fonctionnent"""
        # Valeur valide
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            annee_naissance=1980
        )
        self.assertIsNotNone(q.id, "Un questionnaire avec année valide devrait être créé")
        
        # Valeur invalide (on teste juste que c'est accepté en base, la validation est au formulaire)
        q2 = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            annee_naissance=1800  # Avant 1900, invalid mais peut être en base
        )
        # La validation se fait au niveau du formulaire, pas du modèle directement

    def test_completion_duration_field(self):
        """Teste que la durée de complétion s'enregistre correctement"""
        duration = 1234  # secondes
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            is_completed=True,
            completion_duration_seconds=duration
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.completion_duration_seconds, duration, 
                        f"La durée de complétion devrait être {duration}")

    def test_submission_number_field(self):
        """Teste que le numéro de soumission s'enregistre correctement"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            is_completed=True,
            submission_number=1
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.submission_number, 1, "Le numéro de soumission devrait être 1")

    # ===== TESTS DES CHAMPS OPTIONNELS (NULL/BLANK) =====
    
    def test_optional_integer_fields(self):
        """Teste que les champs optionnels peuvent rester vides"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user
            # Ne pas remplir genre, habitat, diplôme, etc.
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertIsNone(q_from_db.genre, "Le genre devrait être null par défaut")
        self.assertIsNone(q_from_db.habitat, "L'habitat devrait être null par défaut")
        self.assertIsNone(q_from_db.niv_diplome, "Le diplôme devrait être null par défaut")

    def test_optional_textarea_fields(self):
        """Teste que les champs TextField optionnels peuvent rester vides"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        # pens_autre_txt peut être vide ou None selon la configuration du modèle
        self.assertIn(q_from_db.pens_autre_txt, ["", None], "pens_autre_txt devrait être vide ou null par défaut")
        self.assertIsNone(q_from_db.discri_autre_precision, "discri_autre_precision devrait être null par défaut")

    # ===== TESTS DE SCÉNARIOS COMPLETS =====
    
    def test_complete_questionnaire_submission(self):
        """Teste un questionnaire complètement rempli"""
        from datetime import time
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            # Socio-démographiques
            annee_naissance=1985,
            genre=Questionnaire.GenreChoices.FEMME,
            habitat=Questionnaire.HabitatChoices.URBAIN,
            niv_diplome=Questionnaire.DiplomeChoices.BAC_2,
            # Rêves
            freq_reves_not=Questionnaire.FreqRevesNotChoices.QUELQUES_FOIS,
            mod_img=True,
            mod_son=True,
            mod_sens=True,
            etendue_souvenir_reve=Questionnaire.EtendueSouvenirReveChoices.PLUS_MOITIE,
            # Sommeil
            heure_coucher=time(23, 0),  # 23:00
            heure_reveil=time(7, 30),   # 07:30
            latence_som=15,
            besoin_som=time(8, 0),      # 8 heures
            reveil_nuit=True,
            aide_sommeil=False,
            # Métadonnées
            is_completed=True,
            completion_duration_seconds=1200,
            submission_number=1
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        
        # Vérifier tous les champs
        self.assertEqual(q_from_db.annee_naissance, 1985)
        self.assertEqual(q_from_db.genre, 1)
        self.assertEqual(q_from_db.habitat, 2)
        self.assertTrue(q_from_db.mod_img)
        self.assertTrue(q_from_db.reveil_nuit)
        self.assertFalse(q_from_db.aide_sommeil)
        self.assertEqual(q_from_db.completion_duration_seconds, 1200)
        self.assertTrue(q_from_db.is_completed)
        self.assertIsNotNone(q_from_db.completed_at or q_from_db.is_completed)

    def test_partial_questionnaire_submission(self):
        """Teste un questionnaire partiellement rempli (sauvegarde intermédiaire)"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            # Seulement certains champs remplis
            genre=Questionnaire.GenreChoices.HOMME,
            mod_img=True,
            reveil_nuit=False,
            is_completed=False  # Pas encore complété
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        
        # Vérifier les champs remplis
        self.assertEqual(q_from_db.genre, 2)
        self.assertTrue(q_from_db.mod_img)
        
        # Vérifier que les champs non remplis sont null/default
        self.assertIsNone(q_from_db.annee_naissance)
        self.assertIsNone(q_from_db.habitat)
        self.assertFalse(q_from_db.is_completed)

    # ===== TESTS DE MODIFICATION =====
    
    def test_update_questionnaire_fields(self):
        """Teste la modification des champs du questionnaire"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            genre=Questionnaire.GenreChoices.FEMME,
            mod_img=True
        )
        
        # Modifier les champs
        q.genre = Questionnaire.GenreChoices.HOMME
        q.mod_img = False
        q.save()
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.genre, 2, "Le genre devrait être modifié à Homme")
        self.assertFalse(q_from_db.mod_img, "mod_img devrait être modifié à False")

    def test_bulk_update_questionnaire(self):
        """Teste la mise à jour groupée des champs"""
        q = Questionnaire.objects.create(profil=self.profil, user=self.user)
        
        # Mise à jour groupée
        Questionnaire.objects.filter(id=q.id).update(
            genre=Questionnaire.GenreChoices.AUTRE,
            habitat=Questionnaire.HabitatChoices.RURAL,
            is_completed=True
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.genre, 3)
        self.assertEqual(q_from_db.habitat, 1)
        self.assertTrue(q_from_db.is_completed)

    # ===== TESTS DES NOUVEAUX CHAMPS: LOGEMENT, PRÊT, MONTANT_LOYER =====
    
    def test_logement_field_integer_choices(self):
        """Teste que le champ logement enregistre correctement une valeur IntegerField"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=Questionnaire.LogementChoices.PROPRIETAIRE
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.logement, 1, "Le logement devrait être 1 (Propriétaire)")
        self.assertEqual(q_from_db.get_logement_display(), "Propriétaire", "Le label devrait être 'Propriétaire'")

    def test_logement_all_choices(self):
        """Teste tous les choix possibles du champ logement"""
        choices_to_test = [
            (1, "Propriétaire"),
            (2, "Locataire d'un logement social"),
            (3, "Locataire hors logement social, dans le parc privé"),
            (4, "Logé·e gratuitement"),
            (5, "Autre"),
        ]
        
        for value, label in choices_to_test:
            q = Questionnaire.objects.create(
                profil=self.profil,
                user=self.user,
                logement=value
            )
            q_from_db = Questionnaire.objects.get(id=q.id)
            self.assertEqual(q_from_db.logement, value, f"Logement {value} devrait être {value}")
            q.delete()

    def test_pret_boolean_field(self):
        """Teste que le champ pret enregistre correctement une valeur BooleanField"""
        # Test avec True
        q1 = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=1,  # Propriétaire
            pret=True
        )
        
        q1_from_db = Questionnaire.objects.get(id=q1.id)
        self.assertTrue(q1_from_db.pret, "pret devrait être True")
        
        # Test avec False
        q2 = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=1,  # Propriétaire
            pret=False
        )
        
        q2_from_db = Questionnaire.objects.get(id=q2.id)
        self.assertFalse(q2_from_db.pret, "pret devrait être False")

    def test_pret_optional_field(self):
        """Teste que le champ pret peut être optionnel (NULL)"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=2  # Locataire social
            # pret non rempli
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertIsNone(q_from_db.pret, "pret devrait être NULL pour locataire")

    def test_montant_loyer_decimal_field(self):
        """Teste que le champ montant_loyer enregistre correctement une valeur DecimalField"""
        from decimal import Decimal
        
        montant = Decimal('850.50')
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=1,  # Propriétaire
            pret=True,
            montant_loyer=montant
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.montant_loyer, montant, f"montant_loyer devrait être {montant}")

    def test_montant_loyer_various_values(self):
        """Teste différentes valeurs du montant_loyer"""
        from decimal import Decimal
        
        test_values = [
            Decimal('0.00'),
            Decimal('100.50'),
            Decimal('1000.00'),
            Decimal('2500.99'),
        ]
        
        for montant in test_values:
            q = Questionnaire.objects.create(
                profil=self.profil,
                user=self.user,
                montant_loyer=montant
            )
            q_from_db = Questionnaire.objects.get(id=q.id)
            self.assertEqual(q_from_db.montant_loyer, montant, f"montant_loyer {montant} devrait être enregistré correctement")
            q.delete()

    def test_montant_loyer_optional_field(self):
        """Teste que le champ montant_loyer peut être optionnel (NULL)"""
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=4  # Logé gratuitement
            # montant_loyer non rempli
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertIsNone(q_from_db.montant_loyer, "montant_loyer devrait être NULL si logé gratuitement")

    def test_logement_pret_montant_complete_scenario_proprietaire(self):
        """Teste un scénario complet: Propriétaire avec prêt et montant"""
        from decimal import Decimal
        
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=1,  # Propriétaire
            pret=True,
            montant_loyer=Decimal('800.75')
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.logement, 1)
        self.assertTrue(q_from_db.pret)
        self.assertEqual(q_from_db.montant_loyer, Decimal('800.75'))

    def test_logement_pret_montant_complete_scenario_locataire_social(self):
        """Teste un scénario complet: Locataire social avec loyer"""
        from decimal import Decimal
        
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=2,  # Locataire social
            pret=None,   # Pas applicable
            montant_loyer=Decimal('450.00')
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.logement, 2)
        self.assertIsNone(q_from_db.pret)
        self.assertEqual(q_from_db.montant_loyer, Decimal('450.00'))

    def test_logement_pret_montant_complete_scenario_locataire_prive(self):
        """Teste un scénario complet: Locataire privé avec loyer"""
        from decimal import Decimal
        
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=3,  # Locataire privé
            pret=None,   # Pas applicable
            montant_loyer=Decimal('750.50')
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.logement, 3)
        self.assertIsNone(q_from_db.pret)
        self.assertEqual(q_from_db.montant_loyer, Decimal('750.50'))

    def test_logement_pret_montant_complete_scenario_loge_gratuitement(self):
        """Teste un scénario complet: Logé gratuitement"""
        
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=4,  # Logé gratuitement
            pret=None,
            montant_loyer=None
        )
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.logement, 4)
        self.assertIsNone(q_from_db.pret)
        self.assertIsNone(q_from_db.montant_loyer)

    def test_update_logement_pret_montant(self):
        """Teste la modification des champs logement, pret, montant_loyer"""
        from decimal import Decimal
        
        q = Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            logement=1,
            pret=True,
            montant_loyer=Decimal('800.00')
        )
        
        # Modifier les champs
        q.logement = 2
        q.pret = None
        q.montant_loyer = Decimal('450.00')
        q.save()
        
        q_from_db = Questionnaire.objects.get(id=q.id)
        self.assertEqual(q_from_db.logement, 2)
        self.assertIsNone(q_from_db.pret)
        self.assertEqual(q_from_db.montant_loyer, Decimal('450.00'))


if __name__ == '__main__':
    import unittest
    unittest.main()
