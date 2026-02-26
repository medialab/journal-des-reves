from django import forms
from .models import Reve, Questionnaire, Emotion, Tag


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
            'niv_diplome',
            'revenus_tranche',
            'travail_statut',
            'profession',
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
            'niv_diplome': forms.Select(attrs={
                'class': 'form-input'
            }),
            'revenus_tranche': forms.Select(attrs={
                'class': 'form-input'
            }),
            'travail_statut': forms.Select(attrs={
                'class': 'form-input',
                'id': 'travail_statut'
            }),
            'profession': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': '3',
                'placeholder': 'Décrivez votre profession'
            }),
            'frequency': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'dream_lucide': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'dream_recurrent': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'dream_nightmare': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'dream_pleasant': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'sleep_quality': forms.Select(attrs={
                'class': 'form-input',
                'id': 'sleep-quality'
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
