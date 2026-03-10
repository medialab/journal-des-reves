from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Reve, Questionnaire, Profil


class ReveForm(forms.ModelForm):
    class Meta:
        model = Reve
        fields = ['audio', 'type_reve', 'etendue_reve', 'sens', 'emotions_reve', 'tags']
        widgets = {
            'audio': forms.FileInput(
                attrs={
                    'accept': 'audio/*',
                }
            ),
            'type_reve': forms.RadioSelect(),
            'etendue_reve': forms.RadioSelect(),
            'sens': forms.RadioSelect(),
            'emotions_reve': forms.CheckboxSelectMultiple(),
            'tags': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'audio': 'Enregistrement audio',
            'type_reve': 'Type de rêve',
            'etendue_reve': 'Je me souviens plutôt',
            'sens': 'Sens présents dans le rêve',
            'emotions_reve': 'Émotions ressenties',
            'tags': 'Tags personnalisés',
        }


class QuestionnaireForm(forms.ModelForm):
    """Formulaire pour le questionnaire sur les rêves"""
    
    class Meta:
        model = Questionnaire
        fields = [
            # PARTIE 1: Variables socio-démographiques
            'annee_naissance',
            'genre',
            'habitat',
            'niv_diplome',
            'revenus_tranche',
            'travail_statut',
            'a_deja_travaille',
            'profession',
            'fonction_management',
            # PARTIE 2: Questions sur les rêves
            'frequency', 
            'dream_lucide', 
            'dream_recurrent', 
            'dream_nightmare', 
            'dream_pleasant',
            'sleep_quality',
            'sleep_hours',
            'comments'
        ]
        
        widgets = {
            'annee_naissance': forms.NumberInput(attrs={
                'class': 'form-input',
                'type': 'number',
                'min': '1900',
                'max': '2025',
                'placeholder': 'AAAA'
            }),
            'genre': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'habitat': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'niv_diplome': forms.Select(attrs={
                'class': 'form-input'
            }),
            'revenus_tranche': forms.Select(attrs={
                'class': 'form-input'
            }),
            'travail_statut': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_travail_statut'
            }),
            'a_deja_travaille': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'profession': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': '3',
                'placeholder': 'Décrivez votre profession'
            }),
            'fonction_management': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'frequency': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'dream_lucide': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'dream_recurrent': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'dream_nightmare': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'dream_pleasant': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'sleep_quality': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_sleep_quality'
            }),
            'sleep_hours': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'sleep-hours',
                'min': '1',
                'max': '24',
                'placeholder': 'Nombre d\'heures'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-textarea',
                'id': 'comments',
                'rows': '5',
                'placeholder': 'Partagez vos observations sur vos rêves...'
            }),
        }
        
        labels = {
            'annee_naissance': 'Année de naissance',
            'genre': 'Genre',
            'niv_diplome': 'Quel est votre diplôme le plus élevé ?',
            'revenus_tranche': 'Revenus mensuels du ménage',
            'travail_statut': 'Situation principale vis-à-vis du travail',
            'profession': 'Profession',
            'frequency': 'À quelle fréquence vous souvenez-vous de vos rêves ?',
            'dream_lucide': 'Rêves lucides',
            'dream_recurrent': 'Rêves récurrents',
            'dream_nightmare': 'Cauchemars',
            'dream_pleasant': 'Rêves agréables',
            'sleep_quality': 'Qualité du sommeil',
            'sleep_hours': 'Heures de sommeil',
            'comments': 'Commentaires',
        }

class SignUpForm(UserCreationForm):
    """
    Formulaire d'inscription avec consentement pour l'enquête sur les rêves.
    Utilise UserCreationForm de Django pour la sécurité du mot de passe.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'votre.email@exemple.com'
        }),
        label='Adresse email'
    )
    
    # Champs de consentement
    consent_data_processing = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        label='J\'accepte que mes données soient traitées par l\'équipe de recherche composée de Maud Yaïche et de ses directeurs de recherche.'
    )
    
    consent_password_account = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        label='Je souscris à un compte spécialisé protégé par un mot de passe.'
    )
    
    consent_quote_expressions = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        label='J\'autorise qu\'une partie de mes expressions puisse être citée, étant entendu qu\'il ne sera pas possible de m\'identifier.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom d\'utilisateur'
            }),
        }
        labels = {
            'username': 'Nom d\'utilisateur',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnaliser les labels des champs password
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Entrez un mot de passe sécurisé'
        })
        self.fields['password2'].label = 'Confirmer le mot de passe'
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirmez votre mot de passe'
        })
        
        # Améliorer l'affichage de l'aide sur le mot de passe
        if self.fields['password1'].help_text:
            self.fields['password1'].help_text = 'Votre mot de passe doit contenir au moins 8 caractères et ne pas être uniquement numérique.'
    
    def clean_email(self):
        """Vérifier que l'email n'existe pas déjà (dans User et Profil)"""
        email = self.cleaned_data.get('email')
        
        # Vérifier dans le modèle User
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Un compte avec cet email existe déjà.')
        
        # Vérifier dans le modèle Profil (double protection)
        from .models import Profil
        if Profil.objects.filter(email=email).exists():
            raise forms.ValidationError('Un profil avec cet email existe déjà.')
        
        return email
    
    def clean(self):
        """Vérifier que tous les consentements sont acceptés"""
        cleaned_data = super().clean()
        
        # Les champs required=True sont vérifiés automatiquement,
        # mais on peut ajouter une validation personnalisée si nécessaire
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Sauvegarder l'utilisateur et créer un profil avec les consentements.
        Utilise le hashage sécurisé de Django par défaut (PBKDF2).
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Créer un profil associé avec les consentements
            profil = Profil.objects.create(
                user=user,
                email=user.email,
                # Enregistrer les consentements
                consent_data_processing=self.cleaned_data['consent_data_processing'],
                consent_password_account=self.cleaned_data['consent_password_account'],
                consent_quote_expressions=self.cleaned_data['consent_quote_expressions'],
                consent_date=timezone.now(),
                welcome_email_sent=False  # L'email sera envoyé à la première connexion
            )
        
        return user