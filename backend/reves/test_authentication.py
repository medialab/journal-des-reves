from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class EmailOrUsernameLoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reveur-test",
            email="compte@example.com",
            password="mot-de-passe-test",
        )
        self.user.profil.email = "profil@example.com"
        self.user.profil.save(update_fields=["email"])
        self.login_url = reverse("reves:login")

    def test_login_with_username(self):
        response = self.client.post(
            self.login_url,
            {"username": "reveur-test", "password": "mot-de-passe-test"},
        )

        self.assertRedirects(response, reverse("reves:journal"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_with_user_email(self):
        response = self.client.post(
            self.login_url,
            {"username": "compte@example.com", "password": "mot-de-passe-test"},
        )

        self.assertRedirects(response, reverse("reves:journal"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_with_profile_email(self):
        response = self.client.post(
            self.login_url,
            {"username": "profil@example.com", "password": "mot-de-passe-test"},
        )

        self.assertRedirects(response, reverse("reves:journal"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_with_wrong_password_is_rejected_for_both_identifiers(self):
        for identifier in ("reveur-test", "compte@example.com"):
            with self.subTest(identifier=identifier):
                response = self.client.post(
                    self.login_url,
                    {"username": identifier, "password": "mauvais-mot-de-passe"},
                )

                self.assertEqual(response.status_code, 200)
                self.assertNotIn("_auth_user_id", self.client.session)
