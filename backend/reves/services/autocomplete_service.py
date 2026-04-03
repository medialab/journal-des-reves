"""
Service d'auto-complétion pour les émotions et éléments des rêves.
Charge un dictionnaire statique de suggestions.
"""
import json
import os
from django.conf import settings


class AutocompleteService:
    """Gère l'auto-complétion pour les émotions et éléments personnalisés"""
    
    _emotions_cache = None
    _elements_cache = None
    
    @classmethod
    def load_autocomplete_data(cls):
        """Charge les données d'auto-complétion depuis le fichier JSON"""
        data_file = os.path.join(
            settings.BASE_DIR,
            'reves',
            'fixtures',
            'autocomplete_data.json'
        )
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Données par défaut si le fichier n'existe pas
            return {
                'emotions': [],
                'elements': []
            }
    
    @classmethod
    def get_emotions(cls):
        """Retourne la liste des émotions suggérées (50 émotions)"""
        if cls._emotions_cache is None:
            data = cls.load_autocomplete_data()
            cls._emotions_cache = data.get('emotions', [])
        return cls._emotions_cache
    
    @classmethod
    def get_elements(cls):
        """Retourne la liste des éléments suggérés (50 éléments)"""
        if cls._elements_cache is None:
            data = cls.load_autocomplete_data()
            cls._elements_cache = data.get('elements', [])
        return cls._elements_cache
    
    @classmethod
    def search_emotions(cls, query):
        """
        Recherche les émotions correspondant à la requête (auto-complétion)
        
        Args:
            query (str): Texte saisi par l'utilisateur
            
        Returns:
            list: Liste des émotions correspondantes
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return cls.get_emotions()
        
        emotions = cls.get_emotions()
        return [
            emotion for emotion in emotions
            if query_lower in emotion.lower()
        ]
    
    @classmethod
    def search_elements(cls, query):
        """
        Recherche les éléments correspondant à la requête (auto-complétion)
        
        Args:
            query (str): Texte saisi par l'utilisateur
            
        Returns:
            list: Liste des éléments correspondants
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return cls.get_elements()
        
        elements = cls.get_elements()
        return [
            element for element in elements
            if query_lower in element.lower()
        ]
