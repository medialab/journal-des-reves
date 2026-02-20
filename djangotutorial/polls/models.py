from django.db import models
from django.utils import timezone
from django.contrib import admin
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
    class Genre(models.TextChoices):
        Femme = 'F'
        Homme = 'H'
        Non_binaire = 'NB'
        Autre = 'A'
    name = models.CharField(max_length=100)
    genre = models.fields.CharField(choices=Genre.choices, max_length=(15)) 
    biography = models.fields.CharField(max_length=1000)
    birth_year = models.fields.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2021)])
    deja_ecrit_reve = models.fields.BooleanField(default=True)
    page_officiel = models.fields.URLField(null=True, blank=True)
    email = models.fields.EmailField(error_messages={"invalid": "Saisissez une adresse de courriel valide"})


