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
        help_text="Transcription automatique du rêve"
    )

    intensite = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Rêve de {self.profil.name} - {self.date}"

