from django.db import models
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import User
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator


# PROFIL USER ------------------------

class Profil(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': "Un profil avec cet email existe déjà."
        }
    )

    # Champs de consentement pour l'enquête
    consent_data_processing = models.BooleanField(
        default=False,
        verbose_name="Accepte le traitement des données",
        help_text="J'accepte que mes données soient traitées par l'équipe de recherche"
    )
    consent_password_account = models.BooleanField(
        default=False,
        verbose_name="Accepte un compte protégé par mot de passe",
        help_text="Je souscris à un compte spécialisé protégé par un mot de passe"
    )
    consent_quote_expressions = models.BooleanField(
        default=False,
        verbose_name="Autorize la citation d'expressions",
        help_text="J'autorise qu'une partie de mes expressions puisse être citée"
    )
    
    # Date d'acceptation des consentements
    consent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'acceptation du consentement"
    )

    # Suivi de l'email de bienvenue
    welcome_email_sent = models.BooleanField(
        default=False,
        verbose_name="Email de bienvenue envoyé",
        help_text="Indique si l'email de bienvenue a été envoyé à la première connexion"
    )

    # Date de création du profil
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création du profil"
    )

    def can_access_questionnaire(self):
        """Vérifie si l'utilisateur peut accéder au questionnaire (1 semaine après création)"""
        if not self.created_at:
            return False
        from django.utils import timezone
        one_week_ago = timezone.now() - timezone.timedelta(days=7)
        return self.created_at <= one_week_ago

    def days_until_questionnaire_access(self):
        """Retourne le nombre de jours restants avant l'accès au questionnaire"""
        if not self.created_at:
            return 7
        from django.utils import timezone
        one_week_after_creation = self.created_at + timezone.timedelta(days=7)
        days_remaining = (one_week_after_creation - timezone.now()).days
        return max(0, days_remaining)


# MODELES POUR LES REVES ========================

class ReveImageModalite(models.Model):
    """Modalités d'images que la personne peut se souvenir (couleur, netteté, etc.)"""
    libelle = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Modalité d'image"
    )
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )

    class Meta:
        ordering = ['ordre', 'libelle']
        verbose_name = "Modalité d'image"
        verbose_name_plural = "Modalités d'images"

    def __str__(self):
        return self.libelle


class ReveEmotion(models.Model):
    """Émotions prédéfinies par les chercheurs"""
    libelle = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Émotion"
    )
    emoji = models.CharField(
        max_length=10,
        default='😐',
        verbose_name="Emoji représentant"
    )
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )

    class Meta:
        ordering = ['ordre', 'libelle']
        verbose_name = "Émotion"
        verbose_name_plural = "Émotions"

    def __str__(self):
        return f"{self.emoji} {self.libelle}"


class ReveEmotionCustom(models.Model):
    """Émotions personnalisées par profil"""
    profil = models.ForeignKey(
        Profil,
        on_delete=models.CASCADE,
        related_name="emotions_custom"
    )
    libelle = models.CharField(
        max_length=100,
        verbose_name="Émotion"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['libelle']
        verbose_name = "Émotion personnalisée"
        verbose_name_plural = "Émotions personnalisées"
        unique_together = ('profil', 'libelle')

    def __str__(self):
        return f"{self.libelle} ({self.profil.user.username})"


class ReveElementCustom(models.Model):
    """Elements personnalisés (personnes, lieux, situations) par profil"""
    profil = models.ForeignKey(
        Profil,
        on_delete=models.CASCADE,
        related_name="elements_custom"
    )
    libelle = models.CharField(
        max_length=120,
        verbose_name="Element"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['libelle']
        verbose_name = "Element personnalisé"
        verbose_name_plural = "Elements personnalisés"
        unique_together = ('profil', 'libelle')

    def __str__(self):
        return f"{self.libelle} ({self.profil.user.username})"


class ReveTag(models.Model):
    """Tags personnalisés créés par les utilisateurs"""
    profil = models.ForeignKey(
        Profil,
        on_delete=models.CASCADE,
        related_name="tags"
    )
    libelle = models.CharField(
        max_length=100,
        verbose_name="Tag"
    )
    couleur = models.CharField(
        max_length=7,
        default='#3245bd',
        verbose_name="Couleur du tag",
        help_text="Couleur en format hex (#RRGGBB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        unique_together = ('profil', 'libelle')

    def __str__(self):
        return f"{self.libelle} ({self.profil.user.username})"


# BASE DE DONNEES REVES ========================

class Reve(models.Model):
    """Modèle pour les rêves enregistrés"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reves",
        null=True,
        blank=True
    )
    
    profil = models.ForeignKey(
        Profil,
        on_delete=models.CASCADE,
        related_name="reves"
    )

    date = models.DateField(auto_now_add=True)

    # Indique si la personne a un souvenir de son rêve (True) ou non (False)
    existence_souvenir = models.BooleanField(
        default=True,
        verbose_name="A un souvenir du rêve",
        help_text="False si l'utilisateur n'a aucun souvenir de son rêve cette nuit"
    )

    audio = models.FileField(
        upload_to="reves_audio/",
        blank=True,
        null=True,
        help_text="Enregistrement audio du rêve (WAV)"
    )

    transcription = models.TextField(
        blank=True,
        null=True,
        help_text="Transcription automatique du rêve (générée par Whisper)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    transcription_ready = models.BooleanField(
        default=False,
        help_text="Indique si la transcription a été générée"
    )

    # ===== NOUVELLES VARIABLES =====

    # Types de rêve
    class TypeReve(models.TextChoices):
        TRES_POSITIF = 'tres_positif', 'Rêve très positif'
        POSITIF = 'positif', 'Rêve positif'
        NEUTRE = 'neutre', 'Rêve neutre'
        MAUVAIS = 'mauvais', 'Mauvais rêve'
        CAUCHEMAR = 'cauchemar', 'Cauchemar'

    type_reve = models.CharField(
        max_length=20,
        choices=TypeReve.choices,
        verbose_name="Type de rêve",
        null=True,
        blank=True
    )

    # Étendue du rêve (une seule réponse)
    class EtenduReve(models.IntegerChoices):
        INSTANT = 1, 'D\'un instant précis'
        MOINS_MOITIE = 2, 'De moins de la moitié du rêve'
        PLUS_MOITIE = 3, 'De plus de la moitié du rêve'
        INTEGRALITE = 4, 'De l\'intégralité ou quasi-totalité du rêve'

    etendue_reve = models.IntegerField(
        choices=EtenduReve.choices,
        verbose_name="Je me souviens plutôt",
        null=True,
        blank=True
    )

    # Sens présents dans le rêve (peut avoir plusieurs)
    class SensChoices(models.IntegerChoices):
        IMAGES = 1, 'Images'
        SONS = 2, 'Des sons, des voix'
        SENSATIONS = 3, 'Des sensations de mon corps'
        EMOTIONS = 4, 'Des émotions ressenties'
        PENSEES = 5, 'Des pensées ou idées'

    sens = models.IntegerField(
        choices=SensChoices.choices,
        verbose_name="Sens principaux",
        null=True,
        blank=True,
        help_text="Le sens principal dont vous vous souvenez"
    )

    # Modalités des images (si Images sélectionné)
    images_modalites = models.ManyToManyField(
        ReveImageModalite,
        blank=True,
        related_name="reves",
        verbose_name="Modalités des images",
        help_text="Les modalités des images dont vous vous souvenez (couleur, netteté, etc.)"
    )

    # Émotions ressenties (peut avoir plusieurs)
    emotions_reve = models.ManyToManyField(
        ReveEmotion,
        blank=True,
        related_name="reves",
        verbose_name="Émotions ressenties"
    )

    emotions_custom = models.ManyToManyField(
        ReveEmotionCustom,
        blank=True,
        related_name="reves",
        verbose_name="Émotions personnalisées"
    )

    # Elements liés au rêve (personnes, lieux, situations), incluant des choix personnalisés
    elements_reve = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Elements liés au rêve",
        help_text="Liste des éléments liés (travail, famille, amis, et personnalisés)"
    )

    class TempsReve(models.TextChoices):
        PASSE_LOINTAIN = 'passe_lointain', 'Passé lointain'
        PASSE_RECENT = 'passe_recent', 'Passé récent (dans la semaine)'
        VEILLE = 'veille', 'Evénements de la veille'
        FUTUR_PROCHE = 'futur_proche', 'Futur proche (dans la semaine)'
        FUTUR_LOINTAIN = 'futur_lointain', 'Futur lointain'
        DIFFICILE = 'difficile', 'Difficile à dire / Pas liés'

    temps_reve = models.CharField(
        max_length=20,
        choices=TempsReve.choices,
        verbose_name="Temporalité des éléments du rêve",
        null=True,
        blank=True
    )

    commentaire_libre = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire libre"
    )

    # Tags personnalisés (peut en ajouter plusieurs)
    tags = models.ManyToManyField(
        ReveTag,
        blank=True,
        related_name="reves",
        verbose_name="Tags personnalisés"
    )

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Rêve de {self.profil.user.username} - {self.date}"


# QUESTIONNAIRE ------------------------

class Questionnaire(models.Model):
    """Modèle pour stocker les réponses au questionnaire sur les rêves"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questionnaires",
        null=True,
        blank=True
    )
    
    profil = models.ForeignKey(
        Profil,
        on_delete=models.CASCADE,
        related_name="questionnaires"
    )
    
    # ===== PARTIE 1: VARIABLES SOCIO-DÉMOGRAPHIQUES =====
    
    # Année de naissance
    annee_naissance = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2025)],
        verbose_name="Année de naissance",
        null=True,
        blank=True
    )
    
    # Genre
    class GenreChoices(models.IntegerChoices):
        FEMME = 1, 'Femme'
        HOMME = 2, 'Homme'
        AUTRE = 3, 'Autre'
    
    genre = models.IntegerField(
        choices=GenreChoices.choices,
        verbose_name="Genre",
        null=True,
        blank=True
    )
    
    # Habitat
    class HabitatChoices(models.IntegerChoices):
        RURAL = 1, 'Rural'
        URBAIN = 2, 'Urbain'
    
    habitat = models.IntegerField(
        choices=HabitatChoices.choices,
        verbose_name="Environnement d'habitat",
        null=True,
        blank=True
    )
    
    # Diplôme
    class DiplomeChoices(models.IntegerChoices):
        AUCUN = 1, 'Aucun diplôme'
        CEP = 2, 'Certificat d\'études primaires'
        BEPC = 3, 'BEPC, brevet élémentaire, brevet des collèges, DNB'
        CAP_BEP = 4, 'CAP, BEP ou diplôme de niveau équivalent'
        BREVET_SUP = 5, 'Brevet supérieur, professionnel, de technicien ou d\'enseignement'
        BAC_TECH_PRO = 6, 'Baccalauréat technologique ou professionnel'
        BAC_GENERAL = 7, 'Baccalauréat d\'enseignement général'
        CAPACITE_DROIT = 8, 'Capacité en droit, DAEU, ESEU'
        BAC_2 = 9, 'Bac +2 (BTS, DUT, DEUG, DEUST, etc.)'
        BAC_3_4 = 10, 'Bac +3 ou Bac +4 (Licence, Master, etc.)'
        BAC_5 = 11, 'Bac +5 (Master, DESS, DEA, grande école, etc.)'
        DOCTORAT = 12, 'Doctorat de recherche'
    
    niv_diplome = models.IntegerField(
        choices=DiplomeChoices.choices,
        verbose_name="Diplôme le plus élevé obtenu",
        null=True,
        blank=True
    )
    
    # Revenus du ménage
    class RevenusChoices(models.IntegerChoices):
        MOINS_400 = 1, 'Moins de 400 €'
        MOINS_600 = 2, 'De 400 € à moins de 600 €'
        MOINS_800 = 3, 'De 600 € à moins de 800 €'
        MOINS_1000 = 4, 'De 800 € à moins de 1 000 €'
        MOINS_1200 = 5, 'De 1 000 € à moins de 1 200 €'
        MOINS_1500 = 6, 'De 1 200 € à moins de 1 500 €'
        MOINS_1800 = 7, 'De 1 500 € à moins de 1 800 €'
        MOINS_2000 = 8, 'De 1 800 € à moins de 2 000 €'
        MOINS_2500 = 9, 'De 2 000 € à moins de 2 500 €'
        MOINS_3000 = 10, 'De 2 500 € à moins de 3 000 €'
        MOINS_4000 = 11, 'De 3 000 € à moins de 4 000 €'
        MOINS_6000 = 12, 'De 4 000 € à moins de 6 000 €'
        MOINS_10000 = 13, 'De 6 000 € à moins de 10 000 €'
        PLUS_10000 = 14, '10 000 € ou plus'
    
    revenus_tranche = models.IntegerField(
        choices=RevenusChoices.choices,
        verbose_name="Revenus mensuels du ménage",
        null=True,
        blank=True
    )
    
    # Situation principale vis-à-vis du travail
    class TravailChoices(models.IntegerChoices):
        EN_EMPLOI = 1, 'En emploi'
        EN_ETUDES = 2, 'En études, formation ou stage'
        AU_CHOMAGE = 3, 'Au chômage'
        RETRAITE = 4, 'Retraité(e), préretraité(e)'
        FOYER = 5, 'Homme ou femme au foyer'
        INVALIDITE = 6, 'Inactif(ve) pour invalidité'
        AUTRE_INACTIVITE = 7, 'Autre situation d\'inactivité'
    
    travail_statut = models.IntegerField(
        choices=TravailChoices.choices,
        verbose_name="Situation principale vis-à-vis du travail",
        null=True,
        blank=True
    )
    
    # Avez-vous déjà travaillé à mi-temps pendant 6 mois minimum ?
    a_deja_travaille = models.BooleanField(
        verbose_name="A déjà travaillé (6+ mois)",
        null=True,
        blank=True,
        help_text="Avez-vous déjà travaillé au moins à mi-temps pendant au moins 6 mois ?"
    )
    
    # Profession (sous-catégorie uniquement)
    class ProfessionChoices(models.IntegerChoices):
        CADRES_11 = 101, "1.1 | Chefs d'entreprises, hors hôtellerie, restauration, commerce"
        CADRES_12 = 102, "1.2 | Chefs d'entreprises, hôtellerie, restauration, commerce"
        CADRES_13 = 103, "1.3 | Cadres dirigeants salariés, hors hôtellerie, restauration, commerce"
        CADRES_14 = 104, "1.4 | Cadres dirigeants et gérants, hôtellerie, restauration, commerce"

        INTEL_21 = 201, "2.1 | Ingénieurs et spécialistes des sciences, des techniques, des TIC"
        INTEL_22 = 202, "2.2 | Médecins et professionnels de santé"
        INTEL_23 = 203, "2.3 | Cadres administratifs, financiers et commerciaux"
        INTEL_24 = 204, "2.4 | Professionnels de la justice, des sciences sociales et de la culture"
        INTEL_25 = 205, "2.5 | Enseignants et professionnels de l'enseignement"

        INTER_31 = 301, "3.1 | Professions intermédiaires des sciences, techniques et TIC"
        INTER_32 = 302, "3.2 | Professions intermédiaires salariées de la santé"
        INTER_33 = 303, "3.3 | Professions intermédiaires de finance, vente et administration"
        INTER_34 = 304, "3.4 | Professions intermédiaires des services juridiques et sociaux"
        INTER_35 = 305, "3.5 | Sous-officiers des forces armées"

        NONSAL_41 = 401, "4.1 | Exploitants agricoles"
        NONSAL_42 = 402, "4.2 | Commerçants et assimilés"
        NONSAL_43 = 403, "4.3 | Artisans"

        EMP_51 = 501, "5.1 | Employés de bureau et assimilés"
        EMP_52 = 502, "5.2 | Employés de réception, guichetiers et assimilés"
        EMP_53 = 503, "5.3 | Aides-soignants, gardes d'enfants et aides-enseignants"
        EMP_54 = 504, "5.4 | Services de protection/sécurité et armées"

        OUV_61 = 601, "6.1 | Ouvriers qualifiés de la construction, sauf électriciens"
        OUV_62 = 602, "6.2 | Ouvriers qualifiés alimentation, bois, habillement"
        OUV_63 = 603, "6.3 | Ouvriers qualifiés métallurgie, mécanique, imprimerie, élec/électronique"
        OUV_64 = 604, "6.4 | Conducteurs de machines/installations fixes, assemblage"
        OUV_65 = 605, "6.5 | Conducteurs de véhicules et engins mobiles"

        PEU_71 = 701, "7.1 | Personnels de services et employés de commerces"
        PEU_72 = 702, "7.2 | Ouvriers peu qualifiés et manœuvres"
        PEU_73 = 703, "7.3 | Agents d'entretien"
        PEU_74 = 704, "7.4 | Ouvriers agricoles"

    profession = models.IntegerField(
        choices=ProfessionChoices.choices,
        verbose_name="Profession (sous-catégorie)",
        blank=True,
        null=True,
        help_text="Choisir uniquement une sous-catégorie de profession"
    )
    
    # Exercez-vous une fonction de management/autorité ?
    fonction_management = models.BooleanField(
        verbose_name="Fonction de management/autorité",
        null=True,
        blank=True,
        help_text="Exercez-vous une fonction de management ou d'autorité ?"
    )
    
    # ===== PARTIE 2: QUESTIONS SUR LES RÊVES ET LE SOMMEIL =====
    
    # Fréquence de rappel des rêves
    class FrequencyChoices(models.TextChoices):
        DAILY = 'daily', 'Tous les jours'
        OFTEN = 'often', 'Souvent'
        SOMETIMES = 'sometimes', 'Parfois'
        RARELY = 'rarely', 'Rarement'
    
    frequency = models.CharField(
        max_length=20,
        choices=FrequencyChoices.choices,
        verbose_name="Fréquence de rappel des rêves",
        null=True,
        blank=True
    )
    
    # Types de rêves
    dream_lucide = models.BooleanField(default=False, verbose_name="Rêves lucides")
    dream_recurrent = models.BooleanField(default=False, verbose_name="Rêves récurrents")
    dream_nightmare = models.BooleanField(default=False, verbose_name="Cauchemars")
    dream_pleasant = models.BooleanField(default=False, verbose_name="Rêves agréables")
    
    # Qualité du sommeil
    class SleepQualityChoices(models.TextChoices):
        EXCELLENT = 'excellent', 'Excellent'
        GOOD = 'good', 'Bon'
        AVERAGE = 'average', 'Moyen'
        POOR = 'poor', 'Mauvais'
    
    sleep_quality = models.CharField(
        max_length=20,
        choices=SleepQualityChoices.choices,
        verbose_name="Qualité du sommeil",
        null=True,
        blank=True
    )
    
    # Heures de sommeil
    sleep_hours = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name="Heures de sommeil",
        null=True,
        blank=True
    )
    
    # Commentaires
    comments = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaires"
    )

    # ===== PARTIE 3: CONDITIONS SOCIALES DU REVE ET DU SOMMEIL =====
    # Groupes logiques:
    # - pratiques_reves
    # - perception_reves
    # - temps_sommeil
    # - problemes_sommeil
    # - avant_dormir

    # pratiques_reves
    class FreqRevesNotChoices(models.IntegerChoices):
        OUI_SOUVENT = 1, 'Oui souvent'
        QUELQUES_FOIS = 2, 'Quelques fois'
        JAMAIS = 3, 'Jamais'

    freq_reves_not = models.IntegerField(
        choices=FreqRevesNotChoices.choices,
        null=True,
        blank=True,
        verbose_name="Avant cette enquête, vous est-il arrivé de noter vos rêves ?"
    )

    # perception_reves
    mod_img = models.BooleanField(default=False, verbose_name='Images')
    mod_son = models.BooleanField(default=False, verbose_name='Sons, voix')
    mod_sens = models.BooleanField(default=False, verbose_name='Sensations du corps')
    mod_emot = models.BooleanField(default=False, verbose_name='Emotions ressenties')
    mod_pens = models.BooleanField(default=False, verbose_name='Pensees ou idees')

    img_coul = models.BooleanField(default=False, verbose_name='En couleur')
    img_nb = models.BooleanField(default=False, verbose_name='En noir et blanc')
    img_net = models.BooleanField(default=False, verbose_name='Nettes')
    img_flou = models.BooleanField(default=False, verbose_name='Floues')
    img_ns = models.BooleanField(default=False, verbose_name='Ne sait pas')

    class EtendueSouvenirReveChoices(models.IntegerChoices):
        SENSATION = 1, 'Une sensation'
        INSTANT_PRECIS = 2, 'Un instant precis'
        MOINS_MOITIE = 3, 'Moins de la moitie de mon reve'
        PLUS_MOITIE = 4, 'Plus de la moitie de mon reve'
        INTEGRALITE = 5, 'L\'integralite'

    etendue_souvenir_reve = models.IntegerField(
        choices=EtendueSouvenirReveChoices.choices,
        null=True,
        blank=True,
        verbose_name="Vous vous souvenez plutôt"
    )

    class TempsDuReveChoices(models.IntegerChoices):
        PASSE_LOINTAIN = 1, 'Du passe lointain'
        PASSE_PROCHE = 2, 'Du passe proche'
        PRESENT_VEILLE = 3, 'Du present (de la veille)'
        FUTUR = 4, 'Du futur (de ce qui pourrait arriver)'
        AUCUN_LIEN = 5, 'Pas de lien avec votre vie'

    temps_du_reve = models.IntegerField(
        choices=TempsDuReveChoices.choices,
        null=True,
        blank=True,
        verbose_name="Vous avez l'impression de rêver davantage"
    )

    # temps_sommeil
    heure_coucher = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Le plus souvent, en semaine, à quelle heure éteignez-vous votre lampe pour dormir ?"
    )

    heure_reveil = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Le plus souvent en semaine à quelle heure vous réveillez-vous ?"
    )

    latence_som = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        verbose_name="Le plus souvent, combien de temps vous faut-il pour vous endormir ?"
    )

    besoin_som = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        verbose_name="En moyenne, de combien de temps de sommeil avez-vous besoin pour être en forme le lendemain ?"
    )

    # problemes_sommeil
    reveil_nuit = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Vous arrive-t-il de vous réveiller la nuit avec des difficultés pour vous rendormir ?"
    )

    nuits_reveil = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(7)],
        verbose_name="Combien de nuits par semaine cela vous arrive-t-il ?"
    )

    duree_eveil = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        verbose_name="En général, combien de temps restez-vous éveillé(e) au cours de la nuit ?"
    )

    aide_sommeil = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Utilisez-vous des aides pour dormir (médicaments, tisane, application de méditation, etc.) ?"
    )

    aide_medic = models.BooleanField(default=False, verbose_name='Médicaments')
    aide_tisane = models.BooleanField(default=False, verbose_name='Tisane')
    aide_autre = models.BooleanField(default=False, verbose_name='Autre aide')

    # avant_dormir
    pens_trav = models.BooleanField(default=False, verbose_name='Travail / etudes')
    pens_fin = models.BooleanField(default=False, verbose_name='Situation financiere')
    pens_fam = models.BooleanField(default=False, verbose_name='Famille')
    pens_proch = models.BooleanField(default=False, verbose_name='Proches')
    pens_actu = models.BooleanField(default=False, verbose_name='Actualite')
    pens_autre = models.BooleanField(default=False, verbose_name='Autre')
    pens_rien = models.BooleanField(default=False, verbose_name='Je ne pense pas a des choses en particulier')
    pens_autre_txt = models.TextField(blank=True, null=True, verbose_name='Precisez autre pensee')

    cont_tv = models.BooleanField(default=False, verbose_name='Television')
    cont_series_films = models.BooleanField(default=False, verbose_name='Series / films')
    cont_rs = models.BooleanField(default=False, verbose_name='Reseaux sociaux')
    cont_jeux = models.BooleanField(default=False, verbose_name='Jeux videos')
    cont_livres = models.BooleanField(default=False, verbose_name='Livres, journaux')
    cont_rien = models.BooleanField(default=False, verbose_name='Rien')
    cont_autre = models.BooleanField(default=False, verbose_name='Autres')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Questionnaire"
        verbose_name_plural = "Questionnaires"
    
    def __str__(self):
        return f"Questionnaire de {self.profil.user.username} - {self.created_at.strftime('%d/%m/%Y')}"

    @property
    def duree_som(self):
        """Duree de sommeil (minutes) = (reveil - coucher) - latence, avec gestion du passage minuit."""
        if not self.heure_coucher or not self.heure_reveil or self.latence_som is None:
            return None

        start_dt = datetime.datetime.combine(datetime.date.today(), self.heure_coucher)
        wake_dt = datetime.datetime.combine(datetime.date.today(), self.heure_reveil)

        if wake_dt <= start_dt:
            wake_dt += datetime.timedelta(days=1)

        total_minutes = int((wake_dt - start_dt).total_seconds() // 60)
        sleep_minutes = total_minutes - int(self.latence_som)
        return max(0, sleep_minutes)

    @property
    def deficit_som(self):
        """Deficit de sommeil (minutes) = duree_som - besoin_som."""
        if self.duree_som is None or self.besoin_som is None:
            return None
        return self.duree_som - int(self.besoin_som)


# MODELE POUR LES NOTIFICATIONS ========================

class Notification(models.Model):
    """Modèle pour tracer les notifications envoyées aux utilisateurs"""
    
    class NotificationType(models.TextChoices):
        DAILY_REMINDER = 'daily_reminder', 'Rappel quotidien - Enregistrer un rêve'
        QUESTIONNAIRE_REMINDER = 'questionnaire_reminder', 'Rappel - Remplir le questionnaire'
        GENERAL = 'general', 'Notification générale'
    
    profil = models.ForeignKey(
        Profil,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        verbose_name="Type de notification"
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name="Titre de la notification"
    )
    
    message = models.TextField(
        verbose_name="Message de la notification"
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name="Notification lue"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de lecture"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.profil.user.username}"
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

