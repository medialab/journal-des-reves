from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Reve, Questionnaire, Profil


class ReveForm(forms.ModelForm):
    class Meta:
        model = Reve
        fields = [
            'audio',
            'type_reve',
            'etendue_reve',
            'sens',
            'emotions_reve',
            'temps_reve',
            'commentaire_libre',
            'tags'
        ]
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
            'temps_reve': forms.RadioSelect(),
            'commentaire_libre': forms.Textarea(attrs={'rows': 4}),
            'tags': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'audio': 'Enregistrement audio',
            'type_reve': 'Type de rêve',
            'etendue_reve': 'Je me souviens plutôt',
            'sens': 'Sens présents dans le rêve',
            'emotions_reve': 'Émotions ressenties',
            'temps_reve': 'Temporalité des éléments du rêve',
            'commentaire_libre': 'Commentaire libre',
            'tags': 'Tags personnalisés',
        }


class QuestionnaireForm(forms.ModelForm):
    """Formulaire pour le questionnaire sur les rêves"""
    
    class Meta:
        model = Questionnaire
        fields = [
            # CONDITIONS SOCIALES DU REVE ET DU SOMMEIL
            # pratiques_reves
            'freq_reves_not',
            # perception_reves
            'mod_img',
            'mod_son',
            'mod_sens',
            'mod_emot',
            'mod_pens',
            'img_coul',
            'img_nb',
            'img_net',
            'img_flou',
            'img_ns',
            'etendue_souvenir_reve',
            'temps_du_reve',
            # temps_sommeil
            'heure_coucher',
            'heure_reveil',
            'latence_som',
            'besoin_som',
            # problemes_sommeil
            'reveil_nuit',
            'nuits_reveil',
            'duree_eveil',
            'aide_sommeil',
            'aide_medic',
            'aide_tisane',
            'aide_autre',
            # avant_dormir
            'pens_trav',
            'pens_fin',
            'pens_fam',
            'pens_proch',
            'pens_actu',
            'pens_autre',
            'pens_rien',
            'pens_autre_txt',
            'cont_tv',
            'cont_series_films',
            'cont_rs',
            'cont_jeux',
            'cont_livres',
            'cont_rien',
            'cont_autre',

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
            'freq_reves_not': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'mod_img': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'mod_son': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'mod_sens': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'mod_emot': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'mod_pens': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'img_coul': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'img_nb': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'img_net': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'img_flou': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'img_ns': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'etendue_souvenir_reve': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'temps_du_reve': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'heure_coucher': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'heure_reveil': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'latence_som': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'max': '1440'}),
            'besoin_som': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'max': '1440'}),
            'reveil_nuit': forms.RadioSelect(
                choices=((True, 'Oui'), (False, 'Non')),
                attrs={'class': 'radio-input'}
            ),
            'nuits_reveil': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'max': '7'}),
            'duree_eveil': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'max': '1440'}),
            'aide_sommeil': forms.RadioSelect(
                choices=((True, 'Oui'), (False, 'Non')),
                attrs={'class': 'radio-input'}
            ),
            'aide_medic': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'aide_tisane': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'aide_autre': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'pens_trav': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'pens_fin': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'pens_fam': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'pens_proch': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'pens_actu': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'pens_autre': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'pens_rien': forms.CheckboxInput(attrs={'class': 'checkbox-input', 'id': 'id_pens_rien'}),
            'pens_autre_txt': forms.Textarea(attrs={'class': 'form-textarea', 'rows': '3'}),
            'cont_tv': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'cont_series_films': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'cont_rs': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'cont_jeux': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'cont_livres': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'cont_rien': forms.CheckboxInput(attrs={'class': 'checkbox-input', 'id': 'id_cont_rien'}),
            'cont_autre': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),

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
            'profession': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_profession'
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
            'freq_reves_not': 'Avant cette enquête, vous est-il arrivé de noter vos rêves ?',
            'mod_img': 'Images',
            'mod_son': 'Sons, voix',
            'mod_sens': 'Sensations du corps',
            'mod_emot': 'Émotions ressenties',
            'mod_pens': 'Pensées ou idées',
            'img_coul': 'En couleur',
            'img_nb': 'En noir et blanc',
            'img_net': 'Nettes',
            'img_flou': 'Floues',
            'img_ns': 'Ne sait pas',
            'etendue_souvenir_reve': 'Vous vous souvenez plutôt :',
            'temps_du_reve': "Vous avez l'impression de rêver davantage :",
            'heure_coucher': 'Le plus souvent, en semaine, à quelle heure éteignez-vous votre lampe pour dormir ?',
            'heure_reveil': 'Le plus souvent en semaine à quelle heure vous réveillez-vous ?',
            'latence_som': 'Le plus souvent, combien de temps vous faut-il pour vous endormir ? Si immédiatement ou quelques secondes, saisir 0 minute.',
            'besoin_som': 'En moyenne, de combien de temps de sommeil avez-vous besoin pour être en forme le lendemain ?',
            'reveil_nuit': 'Vous arrive-t-il de vous réveiller la nuit avec des difficultés pour vous rendormir ?',
            'nuits_reveil': 'Combien de nuits par semaine cela vous arrive-t-il ?',
            'duree_eveil': 'En général, combien de temps restez-vous éveillé(e) au cours de la nuit ?',
            'aide_sommeil': 'Utilisez-vous des aides pour dormir (médicaments, tisane, application de méditation, etc.) ?',
            'aide_medic': 'Médicaments',
            'aide_tisane': 'Tisane',
            'aide_autre': 'Autre',
            'pens_trav': 'Travail / études',
            'pens_fin': 'Situation financière',
            'pens_fam': 'Famille',
            'pens_proch': 'Proches',
            'pens_actu': 'Actualité',
            'pens_autre': 'Autre',
            'pens_rien': 'Je ne pense pas à des choses en particulier',
            'pens_autre_txt': 'Précisez si autre',
            'cont_tv': 'Télévision',
            'cont_series_films': 'Séries / films',
            'cont_rs': 'Réseaux sociaux',
            'cont_jeux': 'Jeux vidéos',
            'cont_livres': 'Livres, journaux',
            'cont_rien': 'Rien',
            'cont_autre': 'Autres',

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

    def clean(self):
        cleaned_data = super().clean()

        # Condition: si la modalité image n'est pas sélectionnée, vider les sous-choix images.
        if not cleaned_data.get('mod_img'):
            for field_name in ['img_coul', 'img_nb', 'img_net', 'img_flou', 'img_ns']:
                cleaned_data[field_name] = False

        # Condition: réveil nocturne -> nuits_reveil et duree_eveil attendues.
        if cleaned_data.get('reveil_nuit') is True:
            if cleaned_data.get('nuits_reveil') is None:
                self.add_error('nuits_reveil', 'Ce champ est requis si vous vous réveillez la nuit.')
            if cleaned_data.get('duree_eveil') is None:
                self.add_error('duree_eveil', 'Ce champ est requis si vous vous réveillez la nuit.')
        else:
            cleaned_data['nuits_reveil'] = None
            cleaned_data['duree_eveil'] = None

        # Condition: aide_sommeil = False -> vider les sous-options.
        if cleaned_data.get('aide_sommeil') is not True:
            for field_name in ['aide_medic', 'aide_tisane', 'aide_autre']:
                cleaned_data[field_name] = False

        # Contrainte: pens_rien exclusif.
        if cleaned_data.get('pens_rien'):
            other_pens_fields = ['pens_trav', 'pens_fin', 'pens_fam', 'pens_proch', 'pens_actu', 'pens_autre']
            if any(cleaned_data.get(name) for name in other_pens_fields):
                raise forms.ValidationError(
                    "Si 'Je ne pense pas à des choses en particulier' est coché, les autres options de pensée doivent être décochées."
                )

        # Contrainte: cont_rien exclusif.
        if cleaned_data.get('cont_rien'):
            other_cont_fields = ['cont_tv', 'cont_series_films', 'cont_rs', 'cont_jeux', 'cont_livres', 'cont_autre']
            if any(cleaned_data.get(name) for name in other_cont_fields):
                raise forms.ValidationError(
                    "Si 'Rien' est coché, les autres contenus/activités doivent être décochés."
                )

        # Si "Autre" pensée n'est pas coché, on ignore le texte libre.
        if not cleaned_data.get('pens_autre'):
            cleaned_data['pens_autre_txt'] = ''

        return cleaned_data

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