from django import forms
from .models import Reve


class ReveForm(forms.ModelForm):
    class Meta:
        model = Reve
        fields = ['audio', 'intensite']
        widgets = {
            'audio': forms.FileInput(
                attrs={
                    'accept': 'audio/*',
                }
            ),
            'intensite': forms.NumberInput(
                attrs={
                    'type': 'range',
                    'min': '1',
                    'max': '10',
                    'value': '5',
                }
            ),
        }
        labels = {
            'audio': 'Enregistrement audio',
            'intensite': 'Intensité du rêve',
        }
