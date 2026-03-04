from django.urls import path, include
from django.contrib import admin
from . import views

app_name = "polls"

urlpatterns = [
    # Page d'accueil publique
    path("", views.AccueilView.as_view(), name="index"),

    # Journal principal (protection LoginRequiredMixin)
    path("journal/", views.JournalView.as_view(), name="journal"),

    # Page de bienvenue
    path("welcome/", views.WelcomeView.as_view(), name="welcome"),

    #Enregistrement des rêves 
    path("enregistrer/", views.EnregistrerView.as_view(), name="enregistrer"),

    # Description projet et mentions légales 
      path("description/", views.DescriptionView.as_view(), name="description"),

    # Page profil
    path("profil/", views.ProfilView.as_view(), name="profil"),
    # Questionnaire
    path("questionnaire/", views.QuestionnaireView.as_view(), name="questionnaire"),
    # Détail d’un rêve
    path("journal/reve/<int:pk>/", views.ReveDetailView.as_view(), name="reve_detail"),
    # Télécharger l'audio d'un rêve (sécurisé)
    path("journal/reve/<int:reve_id>/audio/", views.ReveAudioDownloadView.as_view(), name="reve_audio"),
    # Mise a jour de la transcription d'un reve
    path("journal/reve/<int:reve_id>/transcription/", views.ReveTranscriptionUpdateView.as_view(), name="reve_transcription_update"),
    
    # Inscription avec consentement
    path("signup/", views.SignUpView.as_view(), name="signup"),
    
    # Auth Django
    path("accounts/", include("django.contrib.auth.urls")),
]