"""
Views pour les APIs d'auto-complétion
"""
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .services.autocomplete_service import AutocompleteService


class AutocompleteEmotionsView(LoginRequiredMixin, View):
    """API endpoint pour l'auto-complétion des émotions"""
    
    def get(self, request):
        """Retourne les suggestions d'émotions basées sur la query"""
        query = request.GET.get('q', '').strip()
        suggestions = AutocompleteService.search_emotions(query)
        
        return JsonResponse({
            'suggestions': suggestions
        })


class AutocompleteElementsView(LoginRequiredMixin, View):
    """API endpoint pour l'auto-complétion des éléments"""
    
    def get(self, request):
        """Retourne les suggestions d'éléments basées sur la query"""
        query = request.GET.get('q', '').strip()
        suggestions = AutocompleteService.search_elements(query)
        
        return JsonResponse({
            'suggestions': suggestions
        })
