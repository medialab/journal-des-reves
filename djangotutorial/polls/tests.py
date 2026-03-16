import datetime

from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Questionnaire, Profil, Reve, ReveEmotion, ReveEmotionCustom, ReveElementCustom, ReveImageModalite, ReveTag
from .forms import QuestionnaireForm


def make_user_with_profil(username='testuser', days_old=10):
    """Crée un User + Profil éligible au questionnaire (créé il y a `days_old` jours)."""
    user = User.objects.create_user(username=username, password='testpass123')
    profil = Profil.objects.create(
        user=user,
        email=f'{username}@test.com',
    )
    # Rétrodate la création pour passer le délai d'attente de 7 jours
    Profil.objects.filter(pk=profil.pk).update(
        created_at=timezone.now() - timezone.timedelta(days=days_old)
    )
    profil.refresh_from_db()
    return user, profil


# ---------------------------------------------------------------------------
# Données POST minimales valides pour chaque section
# ---------------------------------------------------------------------------

SECTION1_DATA = {
    'freq_reves_not': '1',
    # mod_img: pas coché → False
    # reveil_nuit: pas coché → None (optionnel)
    'reveil_nuit': 'False',
    'aide_sommeil': 'False',
}

SECTION2_DATA = {
    'perception_financiere': '2',
    'perception_risque_pauvrete': '2',
    'position_subjective_classe': '3',
    'perception_mobilite': '2',
    'discri_presence': '3',   # Jamais → pas besoin de raison/contexte
    'sante_generale': '2',
    'det_1': '3',
    'det_2': '3',
    'det_3': '3',
    'det_4': '3',
    'det_5': '3',
}

SECTION3_DATA = {
    'annee_naissance': '1985',
    'genre': '1',
    'habitat': '2',
    'niv_diplome': '9',
    'revenus_tranche': '7',
    'travail_statut': '1',
    'profession': '203',
    'fonction_management': 'True',
    'statut_couple': '2',  # Non → pas de questions conjoint
    'lieu_naissance': '1',
    'lieu_naissance_pere': '1',
}

def full_post_data():
    """Construit un POST complet fusionnant toutes les sections."""
    data = {}
    data.update(SECTION1_DATA)
    data.update(SECTION2_DATA)
    data.update(SECTION3_DATA)
    return data


# ===========================================================================
# TESTS DU FORMULAIRE (QuestionnaireForm)
# ===========================================================================

class QuestionnaireFormFieldsTest(TestCase):
    """Vérifie que tous les champs du modèle sont bien dans le formulaire."""

    def test_all_model_fields_in_form(self):
        """Chaque champ du Meta.fields doit exister dans le formulaire instancié."""
        form = QuestionnaireForm()
        for field_name in QuestionnaireForm.Meta.fields:
            self.assertIn(
                field_name, form.fields,
                msg=f"Le champ '{field_name}' est dans Meta.fields mais absent de form.fields"
            )

    def test_form_fields_match_model_fields(self):
        """Chaque champ dans form.fields doit exister sur le modèle Questionnaire."""
        form = QuestionnaireForm()
        model_field_names = {f.name for f in Questionnaire._meta.get_fields()}
        for field_name in form.fields:
            self.assertIn(
                field_name, model_field_names,
                msg=f"Le champ de formulaire '{field_name}' n'existe pas sur le modèle Questionnaire"
            )


class QuestionnaireFormValidationTest(TestCase):
    """Tests de validation du formulaire."""

    def _valid_data(self):
        return full_post_data()

    # --- Soumission valide de base ---
    def test_valid_minimal_form(self):
        data = self._valid_data()
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")

    # --- reveil_nuit conditionnel ---
    def test_reveil_nuit_true_requires_sub_fields(self):
        data = self._valid_data()
        data['reveil_nuit'] = 'True'
        # Pas de nuits_reveil ni duree_eveil → erreurs attendues
        form = QuestionnaireForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nuits_reveil', form.errors)
        self.assertIn('duree_eveil', form.errors)

    def test_reveil_nuit_true_with_sub_fields(self):
        data = self._valid_data()
        data['reveil_nuit'] = 'True'
        data['nuits_reveil'] = '3'
        data['duree_eveil'] = '30'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")

    def test_reveil_nuit_false_clears_sub_fields(self):
        data = self._valid_data()
        data['reveil_nuit'] = 'False'
        data['nuits_reveil'] = '2'
        data['duree_eveil'] = '20'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        # Les sous-champs doivent être effacés par clean()
        self.assertIsNone(form.cleaned_data.get('nuits_reveil'))
        self.assertIsNone(form.cleaned_data.get('duree_eveil'))

    # --- aide_sommeil conditionnel ---
    def test_aide_sommeil_false_clears_subchoices(self):
        data = self._valid_data()
        data['aide_sommeil'] = 'False'
        data['aide_medic'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertFalse(form.cleaned_data.get('aide_medic'))

    def test_aide_sommeil_true_keeps_subchoices(self):
        data = self._valid_data()
        data['aide_sommeil'] = 'True'
        data['aide_tisane'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertTrue(form.cleaned_data.get('aide_tisane'))

    # --- pens_rien exclusif ---
    def test_pens_rien_exclusif_raises_error(self):
        data = self._valid_data()
        data['pens_rien'] = 'on'
        data['pens_trav'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_pens_rien_alone_is_valid(self):
        data = self._valid_data()
        data['pens_rien'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")

    # --- cont_rien exclusif ---
    def test_cont_rien_avec_autre_contenu_raises_error(self):
        data = self._valid_data()
        data['cont_rien'] = 'on'
        data['cont_tv'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertFalse(form.is_valid())

    # --- statut_couple : conj_* effacé si pas en couple ---
    def test_conj_fields_cleared_when_not_in_couple(self):
        data = self._valid_data()
        data['statut_couple'] = '2'  # Non
        data['conj_niv_diplome'] = '5'
        data['conj_csp'] = '203'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertIsNone(form.cleaned_data.get('conj_niv_diplome'))
        self.assertIsNone(form.cleaned_data.get('conj_csp'))

    def test_conj_fields_kept_when_in_couple(self):
        data = self._valid_data()
        data['statut_couple'] = '1'  # Oui
        data['conj_niv_diplome'] = '5'
        data['conj_csp'] = '203'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertEqual(form.cleaned_data.get('conj_niv_diplome'), 5)
        self.assertEqual(form.cleaned_data.get('conj_csp'), 203)

    # --- discri_presence conditionnel ---
    def test_discri_presence_yes_no_raison_raises_error(self):
        data = self._valid_data()
        data['discri_presence'] = '1'  # Oui souvent
        # Pas de raison → erreur
        form = QuestionnaireForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('discri_presence', form.errors)

    def test_discri_presence_yes_with_raison_and_contexte(self):
        data = self._valid_data()
        data['discri_presence'] = '1'
        data['discri_genre'] = 'on'
        data['discri_contexte_travail'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")

    def test_discri_presence_no_clears_detail_fields(self):
        data = self._valid_data()
        data['discri_presence'] = '3'  # Jamais
        data['discri_age'] = 'on'   # Ne devrait pas compter
        data['discri_contexte_emploi'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertFalse(form.cleaned_data.get('discri_age'))
        self.assertFalse(form.cleaned_data.get('discri_contexte_emploi'))

    def test_discri_autre_precision_required_when_discri_autre(self):
        data = self._valid_data()
        data['discri_presence'] = '2'
        data['discri_autre'] = 'on'
        data['discri_contexte_travail'] = 'on'
        # Sans précision → erreur
        form = QuestionnaireForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('discri_autre_precision', form.errors)

    # --- composition_logement_enfants conditionnel ---
    def test_enfants_requires_nb_when_checked(self):
        data = self._valid_data()
        data['composition_logement_enfants'] = 'on'
        # Pas de nb_enfants_cohabitants → erreur
        form = QuestionnaireForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nb_enfants_cohabitants', form.errors)

    def test_enfants_ok_with_nb(self):
        data = self._valid_data()
        data['composition_logement_enfants'] = 'on'
        data['nb_enfants_cohabitants'] = '2'
        data['nb_enfants_moins14'] = '1'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertEqual(form.cleaned_data.get('nb_enfants_cohabitants'), 2)

    def test_nb_enfants_moins14_cannot_exceed_total(self):
        data = self._valid_data()
        data['composition_logement_enfants'] = 'on'
        data['nb_enfants_cohabitants'] = '2'
        data['nb_enfants_moins14'] = '3'  # 3 > 2 → erreur
        form = QuestionnaireForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nb_enfants_moins14', form.errors)

    # --- Test valeurs booléennes --- 
    def test_boolean_checkbox_saves_true_when_present(self):
        data = self._valid_data()
        data['mod_img'] = 'on'
        data['img_coul'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertTrue(form.cleaned_data.get('mod_img'))
        self.assertTrue(form.cleaned_data.get('img_coul'))

    def test_boolean_checkbox_saves_false_when_absent(self):
        data = self._valid_data()
        # mod_img absent du POST
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertFalse(form.cleaned_data.get('mod_img'))

    def test_img_subchoices_cleared_when_no_mod_img(self):
        """Si mod_img n'est pas coché, les sous-champs images doivent être effacés."""
        data = self._valid_data()
        # Pas de mod_img mais img_coul coché
        data['img_coul'] = 'on'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        # clean() doit avoir effacé img_coul
        self.assertFalse(form.cleaned_data.get('img_coul'))

    # --- Test champs integer ---  
    def test_annee_naissance_saves_correctly(self):
        data = self._valid_data()
        data['annee_naissance'] = '1990'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertEqual(form.cleaned_data.get('annee_naissance'), 1990)

    def test_csp_grouped_choices_save_correctly(self):
        """Les valeurs des optgroups CSP (ex. 203) doivent être acceptées."""
        data = self._valid_data()
        data['pere_csp'] = '203'
        data['mere_csp'] = '501'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertEqual(form.cleaned_data.get('pere_csp'), 203)
        self.assertEqual(form.cleaned_data.get('mere_csp'), 501)

    def test_csp_hors_marche_value_accepted(self):
        """Les valeurs 902, 903, 904, 1300 doivent être acceptées."""
        data = self._valid_data()
        data['pere_csp'] = '902'
        data['mere_csp'] = '1300'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertEqual(form.cleaned_data.get('pere_csp'), 902)
        self.assertEqual(form.cleaned_data.get('mere_csp'), 1300)

    def test_a_deja_travaille_lowercase_true_accepted(self):
        """Le formulaire reçoit value='true' (minuscule) depuis le template."""
        data = self._valid_data()
        data['travail_statut'] = '2'  # étudiant → montre a_deja_travaille
        data.pop('profession', None)
        data['a_deja_travaille'] = 'true'   # minuscule - valeur envoyée par le template
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertTrue(form.cleaned_data.get('a_deja_travaille'))

    def test_a_deja_travaille_lowercase_false_accepted(self):
        data = self._valid_data()
        data['a_deja_travaille'] = 'false'  # minuscule
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertFalse(form.cleaned_data.get('a_deja_travaille'))

    def test_fonction_management_lowercase_values(self):
        data = self._valid_data()
        data['fonction_management'] = 'true'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertTrue(form.cleaned_data.get('fonction_management'))

    def test_reveil_nuit_uppercase_true(self):
        data = self._valid_data()
        data['reveil_nuit'] = 'True'
        data['nuits_reveil'] = '2'
        data['duree_eveil'] = '15'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertTrue(form.cleaned_data.get('reveil_nuit'))

    def test_reveil_nuit_uppercase_false(self):
        data = self._valid_data()
        data['reveil_nuit'] = 'False'
        form = QuestionnaireForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Erreurs: {form.errors}")
        self.assertFalse(form.cleaned_data.get('reveil_nuit'))


# ===========================================================================
# TESTS DE LA VUE (QuestionnaireView)
# ===========================================================================

class QuestionnaireViewAjaxSaveTest(TestCase):
    """Teste la sauvegarde AJAX par section."""

    def setUp(self):
        self.client = Client()
        self.user, self.profil = make_user_with_profil()
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('polls:questionnaire')

    def _ajax_post(self, section, data):
        post_data = {'section': str(section), 'section_duration': '30'}
        post_data.update(data)
        return self.client.post(
            self.url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    # --- Création d'un brouillon ---
    def test_ajax_section1_creates_questionnaire_draft(self):
        resp = self._ajax_post('1', SECTION1_DATA)
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content, {'success': True, 'message': 'Section enregistrée.'})
        q = Questionnaire.objects.filter(profil=self.profil).first()
        self.assertIsNotNone(q)
        self.assertFalse(q.is_completed)

    def test_ajax_section1_saves_freq_reves_not(self):
        self._ajax_post('1', {'freq_reves_not': '2'})
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertEqual(q.freq_reves_not, 2)

    def test_ajax_section1_saves_mod_img_true(self):
        self._ajax_post('1', {'mod_img': 'on'})
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertTrue(q.mod_img)

    def test_ajax_section1_saves_mod_img_false_when_absent(self):
        """Checkbox absente du POST → False."""
        data = dict(SECTION1_DATA)
        # Pas de mod_img dans le POST
        self._ajax_post('1', data)
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertFalse(q.mod_img)

    def test_ajax_section1_saves_reveil_nuit_true(self):
        data = {'reveil_nuit': 'True', 'nuits_reveil': '3', 'duree_eveil': '20'}
        self._ajax_post('1', data)
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertTrue(q.reveil_nuit)
        self.assertEqual(q.nuits_reveil, 3)
        self.assertEqual(q.duree_eveil, 20)

    def test_ajax_section1_saves_reveil_nuit_false(self):
        data = {'reveil_nuit': 'False'}
        self._ajax_post('1', data)
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertFalse(q.reveil_nuit)

    def test_ajax_section2_saves_perception_fields(self):
        # D'abord créer le brouillon
        self._ajax_post('1', SECTION1_DATA)
        data = {
            'perception_financiere': '3',
            'discri_presence': '3',
            'sante_generale': '1',
            'det_1': '2',
        }
        self._ajax_post('2', data)
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertEqual(q.perception_financiere, 3)
        self.assertEqual(q.discri_presence, 3)
        self.assertEqual(q.sante_generale, 1)
        self.assertEqual(q.det_1, 2)

    def test_ajax_section2_saves_discri_checkboxes(self):
        self._ajax_post('1', SECTION1_DATA)
        data = {
            'discri_presence': '1',
            'discri_genre': 'on',
            'discri_contexte_travail': 'on',
        }
        self._ajax_post('2', data)
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertTrue(q.discri_genre)
        self.assertTrue(q.discri_contexte_travail)
        self.assertFalse(q.discri_age)  # Non coché → False

    def test_ajax_section3_saves_sociodem_fields(self):
        self._ajax_post('1', SECTION1_DATA)
        self._ajax_post('2', SECTION2_DATA)
        data = {
            'annee_naissance': '1985',
            'genre': '1',
            'habitat': '2',
            'niv_diplome': '9',
            'revenus_tranche': '7',
            'travail_statut': '1',
            'profession': '203',
            'statut_couple': '2',
            'lieu_naissance': '1',
            'lieu_naissance_pere': '2',
        }
        self._ajax_post('3', data)
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertEqual(q.annee_naissance, 1985)
        self.assertEqual(q.genre, 1)
        self.assertEqual(q.habitat, 2)
        self.assertEqual(q.niv_diplome, 9)
        self.assertEqual(q.revenus_tranche, 7)
        self.assertEqual(q.travail_statut, 1)
        self.assertEqual(q.profession, 203)
        self.assertEqual(q.statut_couple, 2)
        self.assertEqual(q.lieu_naissance, 1)
        self.assertEqual(q.lieu_naissance_pere, 2)

    def test_ajax_section3_saves_a_deja_travaille_lowercase_true(self):
        """Valeur 'True' (majuscule) envoyée par le template → doit sauvegarder True (le bug était en minuscule)."""
        self._ajax_post('1', SECTION1_DATA)
        self._ajax_post('2', SECTION2_DATA)
        # Section 3 inclut a_deja_travaille dans SECTION_FIELDS
        data = {'a_deja_travaille': 'True', 'travail_statut': '2'}
        self._ajax_post('3', data)
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertTrue(q.a_deja_travaille)

    def test_ajax_section3_saves_a_deja_travaille_lowercase_false(self):
        """Valeur 'False' (majuscule après fix) → doit sauvegarder False."""
        self._ajax_post('1', SECTION1_DATA)
        self._ajax_post('2', SECTION2_DATA)
        data = {'a_deja_travaille': 'False', 'travail_statut': '2'}
        self._ajax_post('3', data)
        q = Questionnaire.objects.get(profil=self.profil)
        self.assertFalse(q.a_deja_travaille)

    def test_ajax_section_updates_existing_draft(self):
        """Un second appel AJAX pour la même section met à jour le brouillon existant."""
        self._ajax_post('1', {'freq_reves_not': '1'})
        q1_id = Questionnaire.objects.get(profil=self.profil).id
        # Second appel
        self._ajax_post('1', {'freq_reves_not': '3'})
        q2 = Questionnaire.objects.get(profil=self.profil)
        self.assertEqual(q1_id, q2.id)  # Même objet
        self.assertEqual(q2.freq_reves_not, 3)  # Valeur mise à jour

    def test_ajax_requires_login(self):
        self.client.logout()
        resp = self._ajax_post('1', SECTION1_DATA)
        self.assertEqual(resp.status_code, 401)

    def test_ajax_blocked_before_7_days(self):
        """Utilisateur créé il y a seulement 3 jours → accès refusé."""
        user2, profil2 = make_user_with_profil('newcomer', days_old=3)
        client2 = Client()
        client2.login(username='newcomer', password='testpass123')
        resp = client2.post(
            self.url,
            {'section': '1', **SECTION1_DATA},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 403)


class QuestionnaireViewFinalSubmitTest(TestCase):
    """Teste la soumission finale du formulaire complet."""

    def setUp(self):
        self.client = Client()
        self.user, self.profil = make_user_with_profil()
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('polls:questionnaire')

    def _ajax_post(self, section, data):
        post_data = {'section': str(section), 'section_duration': '30'}
        post_data.update(data)
        return self.client.post(
            self.url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    def _final_post(self, data):
        return self.client.post(self.url, data, follow=False)

    def test_full_submission_creates_completed_questionnaire(self):
        """Soumission complète → questionnaire marqué is_completed=True."""
        # Sauvegardes AJAX intermédiaires
        self._ajax_post('1', SECTION1_DATA)
        self._ajax_post('2', SECTION2_DATA)
        # Soumission finale avec toutes les données
        resp = self._final_post(full_post_data())
        self.assertEqual(resp.status_code, 302)
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        self.assertIsNotNone(q.completed_at)

    def test_full_submission_saves_all_section1_fields(self):
        """Vérifie que les champs section 1 sont bien dans le questionnaire final."""
        data = full_post_data()
        data['freq_reves_not'] = '2'
        data['reveil_nuit'] = 'True'
        data['nuits_reveil'] = '4'
        data['duree_eveil'] = '25'
        data['aide_sommeil'] = 'True'
        data['aide_tisane'] = 'on'
        data['mod_img'] = 'on'
        data['img_coul'] = 'on'
        data['pens_trav'] = 'on'
        resp = self._final_post(data)
        self.assertEqual(resp.status_code, 302)
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        self.assertEqual(q.freq_reves_not, 2)
        self.assertTrue(q.reveil_nuit)
        self.assertEqual(q.nuits_reveil, 4)
        self.assertEqual(q.duree_eveil, 25)
        self.assertTrue(q.aide_sommeil)
        self.assertTrue(q.aide_tisane)
        self.assertTrue(q.mod_img)
        self.assertTrue(q.img_coul)
        self.assertTrue(q.pens_trav)

    def test_full_submission_saves_all_section2_fields(self):
        data = full_post_data()
        data['perception_financiere'] = '4'
        data['sante_generale'] = '3'
        data['det_1'] = '2'
        data['det_5'] = '4'
        resp = self._final_post(data)
        self.assertEqual(resp.status_code, 302)
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        self.assertEqual(q.perception_financiere, 4)
        self.assertEqual(q.sante_generale, 3)
        self.assertEqual(q.det_1, 2)
        self.assertEqual(q.det_5, 4)

    def test_full_submission_saves_all_section3_fields(self):
        data = full_post_data()
        data['annee_naissance'] = '1978'
        data['genre'] = '2'
        data['habitat'] = '1'
        data['niv_diplome'] = '11'
        data['revenus_tranche'] = '10'
        data['travail_statut'] = '1'
        data['profession'] = '302'
        data['fonction_management'] = 'True'
        data['statut_couple'] = '2'
        data['composition_logement_conjoint'] = 'on'
        data['lieu_naissance'] = '3'
        data['lieu_naissance_pere'] = '2'
        resp = self._final_post(data)
        self.assertEqual(resp.status_code, 302)
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        self.assertEqual(q.annee_naissance, 1978)
        self.assertEqual(q.genre, 2)
        self.assertEqual(q.habitat, 1)
        self.assertEqual(q.niv_diplome, 11)
        self.assertEqual(q.revenus_tranche, 10)
        self.assertEqual(q.travail_statut, 1)
        self.assertEqual(q.profession, 302)
        self.assertTrue(q.fonction_management)
        self.assertEqual(q.statut_couple, 2)
        self.assertTrue(q.composition_logement_conjoint)
        self.assertEqual(q.lieu_naissance, 3)
        self.assertEqual(q.lieu_naissance_pere, 2)

    def test_full_submission_saves_csp_grouped_choice(self):
        """Les valeurs d'optgroup CSP (102, 504, 902, 1300) doivent être persistées."""
        data = full_post_data()
        data['pere_csp'] = '102'
        data['mere_csp'] = '504'
        resp = self._final_post(data)
        self.assertEqual(resp.status_code, 302)
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        self.assertEqual(q.pere_csp, 102)
        self.assertEqual(q.mere_csp, 504)

    def test_full_submission_saves_hors_marche_csp(self):
        """Valeurs hors marché du travail (902, 1300) doivent être acceptées."""
        data = full_post_data()
        data['pere_csp'] = '902'
        data['mere_csp'] = '1300'
        resp = self._final_post(data)
        self.assertEqual(resp.status_code, 302)
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        self.assertEqual(q.pere_csp, 902)
        self.assertEqual(q.mere_csp, 1300)

    def test_fonction_management_lowercase_true_saved_correctly(self):
        """Template envoie value='true'/'false' en minuscule → doit être sauvegardé."""
        data = full_post_data()
        data['fonction_management'] = 'true'
        resp = self._final_post(data)
        self.assertEqual(resp.status_code, 302)
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        self.assertTrue(q.fonction_management)

    def test_a_deja_travaille_lowercase_saved_correctly(self):
        data = full_post_data()
        data['travail_statut'] = '2'  # En études
        data['a_deja_travaille'] = 'true'
        data.pop('profession', None)
        resp = self._final_post(data)
        self.assertEqual(resp.status_code, 302)
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        self.assertTrue(q.a_deja_travaille)

    def test_invalid_form_does_not_create_completed_questionnaire(self):
        """Un formulaire invalide ne doit pas créer un questionnaire is_completed=True."""
        data = full_post_data()
        data['reveil_nuit'] = 'True'
        # Manque nuits_reveil et duree_eveil → formulaire invalide
        resp = self._final_post(data)
        self.assertEqual(resp.status_code, 200)  # re-render, pas de redirection
        self.assertFalse(Questionnaire.objects.filter(profil=self.profil, is_completed=True).exists())

    def test_session_cleared_after_submit(self):
        """La session doit être vidée après une soumission réussie."""
        # Sauvegardes AJAX pour créer des données en session
        self._ajax_post('1', SECTION1_DATA)
        session_before = self.client.session.get('questionnaire_id')
        self.assertIsNotNone(session_before)
        # Soumission finale
        self._final_post(full_post_data())
        session_after = self.client.session.get('questionnaire_id')
        self.assertIsNone(session_after)

    def test_submission_updates_existing_draft(self):
        """La soumission finale doit mettre à jour le brouillon AJAX, pas créer un doublon."""
        self._ajax_post('1', SECTION1_DATA)
        self._ajax_post('2', SECTION2_DATA)
        count_before = Questionnaire.objects.filter(profil=self.profil).count()
        self._final_post(full_post_data())
        count_after = Questionnaire.objects.filter(profil=self.profil).count()
        self.assertEqual(count_before, count_after)  # Pas de doublon


# ===========================================================================
# TEST END-TO-END : Utilisateur remplit tout le questionnaire
# ===========================================================================

class QuestionnaireEndToEndTest(TestCase):
    """Test complet d'un utilisateur remplissant le questionnaire en entier."""

    def setUp(self):
        self.client = Client()
        self.user, self.profil = make_user_with_profil()
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('polls:questionnaire')

    def _ajax_post(self, section, data):
        post_data = {'section': str(section), 'section_duration': '45'}
        post_data.update(data)
        return self.client.post(
            self.url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

    def test_complete_user_journey(self):
        """
        Test complet : un utilisateur complète les 3 sections et soumet le questionnaire.
        Vérifie que toutes les réponses sont bien enregistrées en base de données.
        """
        
        # ========== Section 1 : Rêves et sommeil ==========
        print("\n✓ Section 1 - Enregistrement des réponses sur les rêves et sommeil")
        section1_data = {
            'freq_reves_not': '1',           # Oui souvent
            'mod_img': 'on',                 # La personne se souvient d'images
            'mod_son': 'on',                 # Et de sons
            'mod_sens': 'on',                # Et de sensations
            'img_coul': 'on',                # Images en couleur
            'img_net': 'on',                 # Images nettes
            'etendue_souvenir_reve': '3',    # Moins de la moitié du rêve
            'temps_du_reve': '2',            # Rêve du passé proche
            'heure_coucher': '23:00',
            'heure_reveil': '07:30',
            'latence_som': '10',             # 10 minutes pour s'endormir
            'besoin_som': '07:30',           # Besoin de 7h30 de sommeil
            'reveil_nuit': 'True',           # Oui, se réveille la nuit
            'nuits_reveil': '2',             # 2 nuits par semaine
            'duree_eveil': '20',             # 20 minutes d'éveil
            'aide_sommeil': 'True',          # Utilise une aide
            'aide_tisane': 'on',             # Une tisane
            'aide_autre': 'on',              # Et autre chose
            'pens_trav': 'on',               # Pense au travail
            'pens_fam': 'on',                # Pense à la famille
            'pens_autre': 'on',              # Pense à autre chose
            'pens_autre_txt': 'Mes projets personnels',
            'cont_series_films': 'on',       # Regarde séries/films
            'cont_rs': 'on',                 # Consulte réseaux sociaux
        }
        resp1 = self._ajax_post('1', section1_data)
        self.assertEqual(resp1.status_code, 200)
        self.assertJSONEqual(resp1.content, {'success': True, 'message': 'Section enregistrée.'})
        
        # ========== Section 2 : Sentiments et discriminations ==========
        print("✓ Section 2 - Enregistrement de la position sociale et santé")
        section2_data = {
            'perception_financiere': '2',    # Ça va
            'perception_risque_pauvrete': '2', # Non plutôt pas
            'position_subjective_classe': '3', # Classes moyennes
            'perception_mobilite': '2',      # Comparable aux parents
            'discri_presence': '2',          # Oui parfois
            'discri_genre': 'on',            # Genre
            'discri_sante_mentale': 'on',    # Santé mentale
            'discri_contexte_travail': 'on', # Sur lieu de travail
            'discri_contexte_sante': 'on',   # Chez médecin
            'sante_generale': '2',           # Bon
            'det_1': '3',                    # Nerveux : quelques fois
            'det_2': '4',                    # Triste : rarement
            'det_3': '2',                    # Calme : souvent
            'det_4': '5',                    # Découragé : jamais
            'det_5': '2',                    # Heureux : souvent
        }
        resp2 = self._ajax_post('2', section2_data)
        self.assertEqual(resp2.status_code, 200)
        self.assertJSONEqual(resp2.content, {'success': True, 'message': 'Section enregistrée.'})
        
        # ========== Section 3 : Données socio-démographiques ==========
        print("✓ Section 3 - Enregistrement des données socio-démographiques")
        section3_data = {
            'annee_naissance': '1988',
            'genre': '1',                    # Femme
            'habitat': '2',                  # Urbain
            'niv_diplome': '10',             # Bac +3/+4
            'revenus_tranche': '8',          # 1800 à 2000€
            'travail_statut': '1',           # En emploi
            'profession': '302',             # Profession intermédiaire santé
            'fonction_management': 'True',   # Oui, fonction management
            'statut_couple': '1',            # Oui en couple
            'composition_logement_conjoint': 'on',
            'composition_logement_enfants': 'on',
            'nb_enfants_cohabitants': '2',
            'nb_enfants_moins14': '1',
            'pere_niv_diplome': '7',         # Bac général
            'pere_csp': '302',               # Profession intermédiaire
            'mere_niv_diplome': '7',         # Bac général
            'mere_csp': '501',               # Employée qualifiée
            'conj_niv_diplome': '9',         # Bac +2
            'conj_csp': '203',               # Cadre admin
            'lieu_naissance': '1',           # France hexagonale
            'lieu_naissance_pere': '1',      # France hexagonale
        }
        resp3 = self._ajax_post('3', section3_data)
        self.assertEqual(resp3.status_code, 200)
        self.assertJSONEqual(resp3.content, {'success': True, 'message': 'Section enregistrée.'})
        
        # ========== Fusion et soumission finale ==========
        print("✓ Soumission finale du questionnaire")
        final_data = {}
        final_data.update(section1_data)
        final_data.update(section2_data)
        final_data.update(section3_data)
        
        resp_final = self.client.post(self.url, final_data, follow=False)
        self.assertEqual(resp_final.status_code, 302)  # Redirection après succès
        
        # ========== Vérification en base de données ==========
        print("✓ Vérification des données en base de données")
        q = Questionnaire.objects.get(profil=self.profil, is_completed=True)
        
        # Section 1
        self.assertEqual(q.freq_reves_not, 1, "freq_reves_not mal enregistré")
        self.assertTrue(q.mod_img, "mod_img mal enregistré")
        self.assertTrue(q.mod_son, "mod_son mal enregistré")
        self.assertTrue(q.mod_sens, "mod_sens mal enregistré")
        self.assertTrue(q.img_coul, "img_coul mal enregistré")
        self.assertTrue(q.img_net, "img_net mal enregistré")
        self.assertEqual(q.etendue_souvenir_reve, 3, "etendue_souvenir_reve mal enregistré")
        self.assertEqual(q.temps_du_reve, 2, "temps_du_reve mal enregistré")
        self.assertEqual(str(q.heure_coucher), '23:00:00', "heure_coucher mal enregistré")
        self.assertEqual(str(q.heure_reveil), '07:30:00', "heure_reveil mal enregistré")
        self.assertEqual(q.latence_som, 10, "latence_som mal enregistré")
        self.assertEqual(str(q.besoin_som), '07:30:00', "besoin_som mal enregistré")
        self.assertTrue(q.reveil_nuit, "reveil_nuit mal enregistré")
        self.assertEqual(q.nuits_reveil, 2, "nuits_reveil mal enregistré")
        self.assertEqual(q.duree_eveil, 20, "duree_eveil mal enregistré")
        self.assertTrue(q.aide_sommeil, "aide_sommeil mal enregistré")
        self.assertTrue(q.aide_tisane, "aide_tisane mal enregistré")
        self.assertTrue(q.aide_autre, "aide_autre mal enregistré")
        self.assertTrue(q.pens_trav, "pens_trav mal enregistré")
        self.assertTrue(q.pens_fam, "pens_fam mal enregistré")
        self.assertTrue(q.pens_autre, "pens_autre mal enregistré")
        self.assertEqual(q.pens_autre_txt, 'Mes projets personnels', "pens_autre_txt mal enregistré")
        self.assertTrue(q.cont_series_films, "cont_series_films mal enregistré")
        self.assertTrue(q.cont_rs, "cont_rs mal enregistré")
        
        # Section 2
        self.assertEqual(q.perception_financiere, 2, "perception_financiere mal enregistré")
        self.assertEqual(q.perception_risque_pauvrete, 2, "perception_risque_pauvrete mal enregistré")
        self.assertEqual(q.position_subjective_classe, 3, "position_subjective_classe mal enregistré")
        self.assertEqual(q.perception_mobilite, 2, "perception_mobilite mal enregistré")
        self.assertEqual(q.discri_presence, 2, "discri_presence mal enregistré")
        self.assertTrue(q.discri_genre, "discri_genre mal enregistré")
        self.assertTrue(q.discri_sante_mentale, "discri_sante_mentale mal enregistré")
        self.assertTrue(q.discri_contexte_travail, "discri_contexte_travail mal enregistré")
        self.assertTrue(q.discri_contexte_sante, "discri_contexte_sante mal enregistré")
        self.assertEqual(q.sante_generale, 2, "sante_generale mal enregistré")
        self.assertEqual(q.det_1, 3, "det_1 mal enregistré")
        self.assertEqual(q.det_2, 4, "det_2 mal enregistré")
        self.assertEqual(q.det_3, 2, "det_3 mal enregistré")
        self.assertEqual(q.det_4, 5, "det_4 mal enregistré")
        self.assertEqual(q.det_5, 2, "det_5 mal enregistré")
        
        # Section 3
        self.assertEqual(q.annee_naissance, 1988, "annee_naissance mal enregistré")
        self.assertEqual(q.genre, 1, "genre mal enregistré")
        self.assertEqual(q.habitat, 2, "habitat mal enregistré")
        self.assertEqual(q.niv_diplome, 10, "niv_diplome mal enregistré")
        self.assertEqual(q.revenus_tranche, 8, "revenus_tranche mal enregistré")
        self.assertEqual(q.travail_statut, 1, "travail_statut mal enregistré")
        self.assertEqual(q.profession, 302, "profession mal enregistré")
        self.assertTrue(q.fonction_management, "fonction_management mal enregistré")
        self.assertEqual(q.statut_couple, 1, "statut_couple mal enregistré")
        self.assertTrue(q.composition_logement_conjoint, "composition_logement_conjoint mal enregistré")
        self.assertTrue(q.composition_logement_enfants, "composition_logement_enfants mal enregistré")
        self.assertEqual(q.nb_enfants_cohabitants, 2, "nb_enfants_cohabitants mal enregistré")
        self.assertEqual(q.nb_enfants_moins14, 1, "nb_enfants_moins14 mal enregistré")
        self.assertEqual(q.pere_niv_diplome, 7, "pere_niv_diplome mal enregistré")
        self.assertEqual(q.pere_csp, 302, "pere_csp mal enregistré")
        self.assertEqual(q.mere_niv_diplome, 7, "mere_niv_diplome mal enregistré")
        self.assertEqual(q.mere_csp, 501, "mere_csp mal enregistré")
        self.assertEqual(q.conj_niv_diplome, 9, "conj_niv_diplome mal enregistré")
        self.assertEqual(q.conj_csp, 203, "conj_csp mal enregistré")
        self.assertEqual(q.lieu_naissance, 1, "lieu_naissance mal enregistré")
        self.assertEqual(q.lieu_naissance_pere, 1, "lieu_naissance_pere mal enregistré")
        
        # Métadonnées
        self.assertTrue(q.is_completed, "Questionnaire ne pas marqué comme complété")
        self.assertIsNotNone(q.completed_at, "completed_at non défini")
        self.assertIsNotNone(q.completion_duration_seconds, "completion_duration_seconds non défini")
        self.assertEqual(q.user, self.user, "user mal lié")
        self.assertEqual(q.profil, self.profil, "profil mal lié")
        
        print("✓ Toutes les données ont été correctement enregistrées!")
        print(f"  - Questionnaire complété en {q.completion_duration_seconds} secondes")
        print(f"  - {q.nb_enfants_cohabitants} enfant(s) sans le foyer, {q.nb_enfants_moins14} de moins de 14 ans")


class QuestionnaireAdminSmokeTest(TestCase):
    """Vérifie que l'admin questionnaires se charge sans erreur."""

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123',
        )
        self.user, self.profil = make_user_with_profil(username='admin-target')
        Questionnaire.objects.create(
            profil=self.profil,
            user=self.user,
            is_completed=True,
            freq_reves_not=1,
            perception_financiere=2,
            perception_risque_pauvrete=2,
            position_subjective_classe=3,
            perception_mobilite=2,
            discri_presence=3,
            sante_generale=2,
            det_1=3,
            det_2=3,
            det_3=3,
            det_4=3,
            det_5=3,
            annee_naissance=1985,
            genre=1,
            habitat=2,
            niv_diplome=9,
            revenus_tranche=7,
            travail_statut=1,
            profession=203,
            fonction_management=True,
            statut_couple=2,
            lieu_naissance=1,
            lieu_naissance_pere=1,
            completed_at=timezone.now(),
        )
        self.client.login(username='admin', password='testpass123')

    def test_admin_index_loads(self):
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)

    def test_questionnaire_changelist_loads(self):
        response = self.client.get(reverse('admin:polls_questionnaire_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Questionnaires')


class ReveAdminSmokeTest(TestCase):
    """Vérifie que l'admin des rêves expose le dashboard et les variables utiles."""

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='dream-admin',
            email='dream-admin@test.com',
            password='testpass123',
        )
        self.user, self.profil = make_user_with_profil(username='dream-target')

        image_modalite = ReveImageModalite.objects.create(libelle='Couleur', ordre=1)
        emotion = ReveEmotion.objects.create(libelle='Joie', emoji='🙂', ordre=1)
        emotion_custom = ReveEmotionCustom.objects.create(profil=self.profil, libelle='Soulagement')
        ReveElementCustom.objects.create(profil=self.profil, libelle='Bureau')
        tag = ReveTag.objects.create(profil=self.profil, libelle='Travail', couleur='#123456')

        reve = Reve.objects.create(
            profil=self.profil,
            user=self.user,
            existence_souvenir=True,
            transcription='J’ai rêvé d’une réunion dans un grand bureau lumineux.',
            transcription_ready=True,
            type_reve=Reve.TypeReve.POSITIF,
            etendue_reve=Reve.EtenduReve.PLUS_MOITIE,
            sens=Reve.SensChoices.IMAGES,
            elements_reve=['Travail', 'Bureau'],
            temps_passe_recent=True,
            temps_futur_proche=True,
            commentaire_libre='Beaucoup de détails visuels.',
        )
        reve.images_modalites.add(image_modalite)
        reve.emotions_reve.add(emotion)
        reve.emotions_custom.add(emotion_custom)
        reve.tags.add(tag)

        self.client.login(username='dream-admin', password='testpass123')

    def test_reve_changelist_loads(self):
        response = self.client.get(reverse('admin:polls_reve_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rêves visibles')
        self.assertContains(response, 'Tonalité agrégée')
        self.assertContains(response, 'Joie')
        self.assertNotContains(response, 'Étendue du souvenir')
        self.assertNotContains(response, 'Sens principal')

    def test_vocab_admin_pages_load(self):
        for view_name in [
            'admin:polls_reveemotion_changelist',
            'admin:polls_reveimagemodalite_changelist',
            'admin:polls_revetag_changelist',
        ]:
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 200)

    def test_reve_export_contains_all_variable_columns(self):
        response = self.client.get(reverse('admin:polls_reve_export_csv'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('images_modalites_labels', content)
        self.assertIn('emotions_custom_labels', content)
        self.assertIn('temporalite_labels', content)