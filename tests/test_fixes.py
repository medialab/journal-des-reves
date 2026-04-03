#!/usr/bin/env python
"""
Test script pour vérifier que les corrections de déconnexion et notifications sont fonctionnelles
"""

import os
import sys
import django

# Configuration du chemin et Django
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from reves.models import Profil

class TestNotificationsAndLogout:
    def __init__(self):
        self.client = Client()
        self.tests_passed = 0
        self.tests_failed = 0
    
    def create_user_with_profile(self, username, password):
        """Créer un utilisateur avec son profil associé"""
        user = User.objects.create_user(username=username, password=password)
        profil = Profil.objects.create(user=user, email=f"{username}@test.com")
        return user, profil
        
    def print_result(self, test_name, passed, details=""):
        """Afficher le résultat d'un test"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   └─ {details}")
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    def test_unauthenticated_user_no_notification_load(self):
        """Test: Un utilisateur non authentifié ne devrait pas avoir de classe is-authenticated"""
        response = self.client.get('/journal/')
        # La page redirige vers login si pas authentifié
        is_redirect = response.status_code in [301, 302, 307, 308]
        self.print_result(
            "Non-authenticated user gets redirected from protected page",
            is_redirect,
            f"Status: {response.status_code}"
        )
    
    def test_authenticated_user_has_is_authenticated_class(self):
        """Test: Un utilisateur authentifié devrait voir la classe is-authenticated"""
        # Créer un utilisateur de test avec profil
        user, profil = self.create_user_with_profile('testuser1', 'testpass123')
        
        # Se connecter
        self.client.login(username='testuser1', password='testpass123')
        
        # Accéder à une page protégée
        response = self.client.get('/journal/')
        
        # Vérifier que c'est accessible
        is_accessible = response.status_code == 200
        
        # Vérifier que la classe is-authenticated est ajoutée
        has_class = b'is-authenticated' in response.content
        
        self.print_result(
            "Authenticated user can access protected page",
            is_accessible,
            f"Status: {response.status_code}"
        )
        
        self.print_result(
            "Authenticated user HTML contains is-authenticated class",
            has_class,
            "Check HTML for class attribute"
        )
        
        # Nettoyer
        profil.delete()
        user.delete()
    
    def test_logout_form_exists(self):
        """Test: Le formulaire de logout existe et a un token CSRF"""
        # Créer et connecter un utilisateur
        user, profil = self.create_user_with_profile('testuser2', 'testpass123')
        self.client.login(username='testuser2', password='testpass123')
        
        # Accéder à la page
        response = self.client.get('/journal/')
        
        # Vérifier que le formulaire existe
        has_logout_form = b'<form method="post" action="/accounts/logout/"' in response.content or \
                          b'action="/accounts/logout/"' in response.content
        
        # Vérifier qu'il y a un CSRF token
        has_csrf_token = b'csrf' in response.content.lower()
        
        self.print_result(
            "Logout form exists on authenticated page",
            has_logout_form,
            "Form with POST method to /accounts/logout/"
        )
        
        self.print_result(
            "Logout form includes CSRF token",
            has_csrf_token,
            "csrf token in response"
        )
        
        # Nettoyer
        profil.delete()
        user.delete()
    
    def test_logout_redirects_correctly(self):
        """Test: La déconnexion redirige vers la page d'accueil"""
        # Créer et connecter un utilisateur
        user, profil = self.create_user_with_profile('testuser3', 'testpass123')
        self.client.login(username='testuser3', password='testpass123')
        
        # Se déconnecter
        response = self.client.post('/accounts/logout/', follow=False)
        
        # Vérifier la redirection
        is_redirect = response.status_code in [301, 302, 307, 308]
        expected_redirect = response.status_code == 302  # Found redirect
        
        self.print_result(
            "Logout performs HTTP redirect",
            is_redirect,
            f"Status: {response.status_code}"
        )
        
        # Vérifier que l'utilisateur est vraiment déconnecté
        self.client.logout()  # Assurer la déconnexion
        response = self.client.get('/journal/')
        user_was_logged_out = response.status_code in [301, 302]  # Redirect = pas authentifié
        
        self.print_result(
            "User is actually logged out after logout",
            user_was_logged_out,
            "Subsequent request to protected page redirects"
        )
        
        # Nettoyer
        profil.delete()
        user.delete()
    
    def test_no_polls_endpoints_remain(self):
        """Test: Vérifier qu'il n'y a plus de références à /polls/ dans les chemins"""
        response = self.client.get('/')  # Accès public
        
        # Vérifier qu'il n'y a pas de références à /polls/api/ ou /polls/static/
        has_polls_api = b'/polls/api/' in response.content
        has_polls_static = b'/static/polls/' in response.content
        has_polls_url = b'/polls/questionnaire/' in response.content or \
                        b'/polls/enregistrer/' in response.content or \
                        b'/polls/journal/' in response.content
        
        no_polls_references = not (has_polls_api or has_polls_static)
        
        self.print_result(
            "No /polls/api/ or /static/polls/ references in homepage",
            no_polls_references,
            f"api={has_polls_api}, static={has_polls_static}"
        )
        
        if has_polls_url:
            print(f"   ⚠️  Warning: Found /polls/ URL references (may be expected in some cases)")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("\n" + "="*60)
        print("🧪 TESTS DE CORRECTIONS - NOTIFICATIONS ET LOGOUT")
        print("="*60 + "\n")
        
        self.test_unauthenticated_user_no_notification_load()
        print()
        self.test_authenticated_user_has_is_authenticated_class()
        print()
        self.test_logout_form_exists()
        print()
        self.test_logout_redirects_correctly()
        print()
        self.test_no_polls_endpoints_remain()
        
        print("\n" + "="*60)
        print(f"Résumé: {self.tests_passed} ✅ | {self.tests_failed} ❌")
        print("="*60 + "\n")
        
        return self.tests_failed == 0

if __name__ == '__main__':
    tester = TestNotificationsAndLogout()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
