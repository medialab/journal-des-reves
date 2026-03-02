from django.db import models
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import User
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    def __str__(self):
        return self.question_text
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
)
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    
# On définit une classe, qu'on nomme choice, on a différent attribut de cette classe, question, voices.? 
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE) # C'est lié à question
    choice_text = models.CharField(max_length=200) #  CHARFIELD = stocke les données de type caractère/texte/chaîne
    # On fixe aussi la longueur maximale des données. 
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.choice_text

class Profil(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    class Genre(models.TextChoices):
        Femme = 'F'
        Homme = 'H'
        Non_binaire = 'NB'
        Autre = 'A'

    name = models.CharField(max_length=100)
    genre = models.CharField(choices=Genre.choices, max_length=15)
    biography = models.TextField()  # mieux que CharField pour long texte
    birth_year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2025)]
    )
    deja_ecrit_reve = models.BooleanField(default=True)
    email = models.EmailField()
    
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

    def __str__(self):
        return self.name


class Reve(models.Model):
    profil = models.ForeignKey(
        Profil,
        on_delete=models.CASCADE,
        related_name="reves"
    )

    date = models.DateField(auto_now_add=True)

    audio = models.FileField(
        upload_to="reves_audio/",
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
        'ImageModalite',
        blank=True,
        related_name="reves",
        verbose_name="Modalités des images",
        help_text="Les modalités des images dont vous vous souvenez (couleur, netteté, etc.)"
    )

    # Émotions ressenties (peut avoir plusieurs)
    emotions_reve = models.ManyToManyField(
        'Emotion',
        blank=True,
        related_name="reves",
        verbose_name="Émotions ressenties"
    )

    emotions_custom = models.ManyToManyField(
        'EmotionCustom',
        blank=True,
        related_name="reves",
        verbose_name="Émotions personnalisées"
    )

    # Tags personnalisés (peut en ajouter plusieurs)
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name="reves",
        verbose_name="Tags personnalisés"
    )

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Rêve de {self.profil.name} - {self.date}"


class ImageModalite(models.Model):
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


class Emotion(models.Model):
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


class EmotionCustom(models.Model):
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
        return f"{self.libelle} ({self.profil.name})"


class Tag(models.Model):
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
        return f"{self.libelle} ({self.profil.name})"


class Questionnaire(models.Model):
    """Modèle pour stocker les réponses au questionnaire sur les rêves"""
    
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
    class GenreChoices(models.TextChoices):
        FEMME = 'F', 'Femme'
        HOMME = 'H', 'Homme'
        AUTRE = 'A', 'Autre'
    
    genre = models.CharField(
        max_length=1,
        choices=GenreChoices.choices,
        verbose_name="Genre",
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
    
    # Profession (texte libre pour plus de flexibilité)
    profession = models.TextField(
        verbose_name="Profession",
        blank=True,
        null=True,
        help_text="Votre profession actuelle ou dernière profession"
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
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Questionnaire"
        verbose_name_plural = "Questionnaires"
    
    def __str__(self):
        return f"Questionnaire de {self.profil.name} - {self.created_at.strftime('%d/%m/%Y')}"

