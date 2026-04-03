from django import forms
import re
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
            'temps_passe_lointain',
            'temps_passe_recent',
            'temps_veille',
            'temps_futur_proche',
            'temps_futur_lointain',
            'temps_difficile',
            'commentaire_libre',
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
            'commentaire_libre': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'audio': 'Enregistrement audio',
            'type_reve': 'Type de rêve',
            'etendue_reve': 'Je me souviens plutôt',
            'sens': 'Sens présents dans le rêve',
            'emotions_reve': 'Émotions ressenties',
            'commentaire_libre': 'Commentaire libre',
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
            'statut_couple',
            'composition_logement_seul',
            'composition_logement_conjoint',
            'composition_logement_enfants',
            'composition_logement_ami_parent_heberge',
            'composition_logement_colocataire',
            'composition_logement_parent_grand_parent',
            'composition_logement_autres',
            'nb_enfants_cohabitants',
            'nb_enfants_moins14',
            'pere_niv_diplome',
            'pere_csp',
            'mere_niv_diplome',
            'mere_csp',
            'conj_niv_diplome',
            'conj_csp',
            'lieu_naissance',
            'lieu_naissance_pere',
            'perception_financiere',
            'perception_risque_pauvrete',
            'position_subjective_classe',
            'perception_mobilite',
            'discri_presence',
            'discri_age',
            'discri_genre',
            'discri_sante_physique',
            'discri_sante_mentale',
            'discri_couleur_peau',
            'discri_origine_nationalite',
            'discri_situation_familiale',
            'discri_orientation_sexuelle',
            'discri_autre',
            'discri_autre_precision',
            'discri_contexte_emploi',
            'discri_contexte_logement',
            'discri_contexte_travail',
            'discri_contexte_education',
            'discri_contexte_sante',
            'discri_contexte_famille',
            'discri_contexte_autre',
            'sante_generale',
            'det_1',
            'det_2',
            'det_3',
            'det_4',
            'det_5',
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
            'besoin_som': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
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
            'statut_couple': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'composition_logement_seul': forms.CheckboxInput(attrs={'class': 'checkbox-input composition-logement-option'}),
            'composition_logement_conjoint': forms.CheckboxInput(attrs={'class': 'checkbox-input composition-logement-option'}),
            'composition_logement_enfants': forms.CheckboxInput(attrs={'class': 'checkbox-input composition-logement-option', 'id': 'id_composition_logement_enfants'}),
            'composition_logement_ami_parent_heberge': forms.CheckboxInput(attrs={'class': 'checkbox-input composition-logement-option'}),
            'composition_logement_colocataire': forms.CheckboxInput(attrs={'class': 'checkbox-input composition-logement-option'}),
            'composition_logement_parent_grand_parent': forms.CheckboxInput(attrs={'class': 'checkbox-input composition-logement-option'}),
            'composition_logement_autres': forms.CheckboxInput(attrs={'class': 'checkbox-input composition-logement-option'}),
            'nb_enfants_cohabitants': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'max': '19'}),
            'nb_enfants_moins14': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'max': '19'}),
            'pere_niv_diplome': forms.Select(attrs={'class': 'form-input'}),
            'pere_csp': forms.Select(attrs={'class': 'form-input'}),
            'mere_niv_diplome': forms.Select(attrs={'class': 'form-input'}),
            'mere_csp': forms.Select(attrs={'class': 'form-input'}),
            'conj_niv_diplome': forms.Select(attrs={'class': 'form-input'}),
            'conj_csp': forms.Select(attrs={'class': 'form-input'}),
            'lieu_naissance': forms.Select(attrs={'class': 'form-input'}),
            'lieu_naissance_pere': forms.Select(attrs={'class': 'form-input'}),
            'perception_financiere': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'perception_risque_pauvrete': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'position_subjective_classe': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'perception_mobilite': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'discri_presence': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'discri_age': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_genre': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_sante_physique': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_sante_mentale': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_couleur_peau': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_origine_nationalite': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_situation_familiale': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_orientation_sexuelle': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_autre': forms.CheckboxInput(attrs={'class': 'checkbox-input', 'id': 'id_discri_autre'}),
            'discri_autre_precision': forms.Textarea(attrs={'class': 'form-textarea', 'rows': '2'}),
            'discri_contexte_emploi': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_contexte_logement': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_contexte_travail': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_contexte_education': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_contexte_sante': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_contexte_famille': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'discri_contexte_autre': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'sante_generale': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'det_1': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'det_2': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'det_3': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'det_4': forms.RadioSelect(attrs={'class': 'radio-input'}),
            'det_5': forms.RadioSelect(attrs={'class': 'radio-input'}),
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
            'duree_eveil': 'En général, combien de temps restez-vous éveillé·e au cours de la nuit ?',
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
            'statut_couple': 'Êtes-vous en couple ?',
            'composition_logement_seul': 'Seul·e',
            'composition_logement_conjoint': 'Avec mon ou ma conjoint·e',
            'composition_logement_enfants': 'Avec un enfant ou des enfants',
            'composition_logement_ami_parent_heberge': 'Avec un·e ami·e ou un parent hébergé',
            'composition_logement_colocataire': 'Avec un·e colocataire',
            'composition_logement_parent_grand_parent': 'Parent ou grand-parent',
            'composition_logement_autres': 'Autres',
            'nb_enfants_cohabitants': 'Combien d’enfants vivent avec vous (même en garde alternée) ?',
            'nb_enfants_moins14': 'Combien ont moins de 14 ans ?',
            'pere_niv_diplome': 'Quel est le plus haut diplôme de votre père ?',
            'pere_csp': 'Votre père est / était...',
            'mere_niv_diplome': 'Quel est le plus haut diplôme de votre mère ?',
            'mere_csp': 'Votre mère est / était plutôt...',
            'conj_niv_diplome': 'Quel est le plus haut diplôme de votre conjoint·e ?',
            'conj_csp': 'Votre conjoint·e est plutôt...',
            'lieu_naissance': 'Où êtes-vous né·e ?',
            'lieu_naissance_pere': 'Où est né votre père ?',
            'perception_financiere': 'Actuellement, dans votre foyer, vous diriez que financièrement :',
            'perception_risque_pauvrete': 'Pensez-vous qu’il y a un risque que vous deveniez pauvre dans les cinq prochaines années ?',
            'position_subjective_classe': 'Aujourd’hui, si vous deviez vous situer socialement, vous diriez que vous appartenez plutôt à :',
            'perception_mobilite': 'Par rapport à vos parents au même âge, diriez-vous que votre situation sociale est :',
            'discri_presence': 'Pensez-vous avoir subi des traitements inégalitaires ou des discriminations au cours des 5 dernières années ?',
            'discri_age': 'Votre âge',
            'discri_genre': 'Votre sexe ou votre genre',
            'discri_sante_physique': 'Votre état de santé physique ou un handicap',
            'discri_sante_mentale': 'Votre état de santé psychique, votre état de santé mentale',
            'discri_couleur_peau': 'Votre couleur de peau',
            'discri_origine_nationalite': 'Vos origines ou votre nationalité',
            'discri_situation_familiale': 'Votre situation de famille (célibataire, enfants en bas âge)',
            'discri_orientation_sexuelle': 'Votre orientation sexuelle',
            'discri_autre': 'Pour une autre raison',
            'discri_autre_precision': 'Précisez',
            'discri_contexte_emploi': 'Lors d’une recherche d’emploi',
            'discri_contexte_logement': 'Lors de la recherche d’un logement',
            'discri_contexte_travail': 'Sur votre lieu de travail',
            'discri_contexte_education': 'A l’école, à l’université ou en formation',
            'discri_contexte_sante': 'Chez un médecin, professionnel de santé ou à l’hôpital',
            'discri_contexte_famille': 'Dans le cadre familial',
            'discri_contexte_autre': 'Lors d’une autre situation',
            'sante_generale': 'Comment est votre état de santé en général ?',
            'det_1': 'Nerveux·se',
            'det_2': 'Triste et abattu·e',
            'det_3': 'Calme et détendu·e',
            'det_4': 'Si découragé·e que rien ne pouvait vous remonter le moral',
            'det_5': 'Heureux·se',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        dropdown_fields = [
            'pere_niv_diplome', 'pere_csp',
            'mere_niv_diplome', 'mere_csp',
            'conj_niv_diplome', 'conj_csp',
            'lieu_naissance', 'lieu_naissance_pere',
        ]

        csp_grouped_fields = {'pere_csp', 'mere_csp', 'conj_csp'}

        def _clean_label(label):
            text = str(label)
            text = re.sub(r'^\d+(?:\.\d+)?\s*\|\s*', '', text)
            text = re.sub(r'^\d+\.\s*', '', text)
            return text.strip()

        for field_name in dropdown_fields:
            if field_name in csp_grouped_fields:
                continue
            field = self.fields.get(field_name)
            if not field:
                continue

            normalized_choices = []
            for value, label in field.choices:
                if value in (None, ''):
                    continue
                normalized_choices.append((value, _clean_label(label)))

            # Remplace l'option "---------" par un libellé propre.
            field.choices = [('', 'Sélectionnez...')] + normalized_choices

        pere_csp_grouped_choices = [
            ('1 | Cadre dirigeant', [
                (101, "1.1 | Chef d'entreprise, hors hôtellerie, restauration, commerce"),
                (102, "1.2 | Chef d'entreprise, hôtellerie, restauration, commerce"),
                (103, "1.3 | Cadre dirigeant salarié, hors hôtellerie, restauration, commerce"),
                (104, "1.4 | Cadre dirigeant et gérant, hôtellerie, restauration, commerce"),
            ]),
            ('2 | Profession intellectuelle et scientifique', [
                (201, "2.1 | Ingénieur et spécialiste des sciences, des techniques, des TIC"),
                (202, "2.2 | Médecin et professionnel de santé"),
                (203, "2.3 | Cadre administratif, financier et commercial"),
                (204, "2.4 | Professionnel de la justice, des sciences sociales et de la culture"),
                (205, "2.5 | Enseignant et professionnel de l’enseignement"),
            ]),
            ('3 | Profession intermédiaire salariée', [
                (301, "3.1 | Profession intermédiaire des sciences, des techniques, des TIC"),
                (302, "3.2 | Profession intermédiaire salariée de la santé"),
                (303, "3.3 | Profession intermédiaire de finance, vente et administration"),
                (304, "3.4 | Profession intermédiaire des services juridiques, des services sociaux et assimilés"),
                (305, "3.5 | Sous-officier des forces armées"),
            ]),
            ('4 | Petit entrepreneur (non-salarié)', [
                (401, '4.1 | Exploitant agricole'),
                (402, '4.2 | Commerçant et assimilé'),
                (403, '4.3 | Artisan'),
            ]),
            ('5 | Employé qualifié', [
                (501, '5.1 | Employé de bureau et assimilé'),
                (502, '5.2 | Employé de réception, guichetier et assimilé'),
                (503, '5.3 | Aide-soignant, garde d’enfant et aide-enseignant'),
                (504, '5.4 | Personnel des services de protection et de sécurité et de l’armée'),
            ]),
            ('6 | Ouvrier qualifié salarié', [
                (601, '6.1 | Ouvrier qualifié de la construction, sauf électricien'),
                (602, "6.2 | Ouvrier qualifié de l'alimentation, du travail sur bois, de l'habillement"),
                (603, "6.3 | Ouvrier qualifié de la métallurgie, de la construction mécanique, de l'imprimerie, de l'électricité et de l'électronique"),
                (604, "6.4 | Conducteur de machines et d'installations fixes, ouvrier qualifié de l'assemblage"),
                (605, '6.5 | Conducteur de véhicules et de matériels et engins mobiles'),
            ]),
            ('7 | Profession salariée peu qualifiée', [
                (701, '7.1 | Personnel de service et employé de commerce'),
                (702, '7.2 | Ouvrier peu qualifié et manœuvre'),
                (703, '7.3 | Agent d\'entretien'),
                (704, '7.4 | Ouvrier agricole'),
            ]),
            ('9 | Hors marché du travail', [
                (902, '9.2 | Personne handicapée inapte de moins de 65 ans'),
                (903, '9.3 | Chômeur non classé dans une autre catégorie'),
                (904, '9.4 | Autre personne hors du marché du travail'),
            ]),
            ('13 | Non réponse', [
                (1300, '13 | Je ne sais pas ou ne peux pas répondre'),
            ]),
        ]

        mere_csp_grouped_choices = [
            ('1 | Cadre dirigeante', [
                (101, "1.1 | Cheffe d'entreprise, hors hôtellerie, restauration, commerce"),
                (102, "1.2 | Cheffe d'entreprise, hôtellerie, restauration, commerce"),
                (103, "1.3 | Cadre dirigeante salariée, hors hôtellerie, restauration, commerce"),
                (104, "1.4 | Cadre dirigeante et gérante, hôtellerie, restauration, commerce"),
            ]),
            ('2 | Profession intellectuelle et scientifique', [
                (201, "2.1 | Ingénieure et spécialiste des sciences, des techniques, des TIC"),
                (202, "2.2 | Médecin et professionnelle de santé"),
                (203, "2.3 | Cadre administrative, financière et commerciale"),
                (204, "2.4 | Professionnelle de la justice, des sciences sociales et de la culture"),
                (205, "2.5 | Enseignante et professionnelle de l’enseignement"),
            ]),
            ('3 | Profession intermédiaire salariée', [
                (301, "3.1 | Profession intermédiaire des sciences, des techniques, des TIC"),
                (302, "3.2 | Profession intermédiaire salariée de la santé"),
                (303, "3.3 | Profession intermédiaire de finance, vente et administration"),
                (304, "3.4 | Profession intermédiaire des services juridiques, des services sociaux et assimilés"),
                (305, "3.5 | Sous-officière des forces armées"),
            ]),
            ('4 | Petite entrepreneure (non-salariée)', [
                (401, '4.1 | Exploitante agricole'),
                (402, '4.2 | Commerçante et assimilée'),
                (403, '4.3 | Artisane'),
            ]),
            ('5 | Employée qualifiée', [
                (501, '5.1 | Employée de bureau et assimilée'),
                (502, '5.2 | Employée de réception, guichetière et assimilée'),
                (503, '5.3 | Aide-soignante, garde d’enfant et aide-enseignante'),
                (504, '5.4 | Personnelle des services de protection et de sécurité et de l’armée'),
            ]),
            ('6 | Ouvrière qualifiée salariée', [
                (601, '6.1 | Ouvrière qualifiée de la construction, sauf électricienne'),
                (602, "6.2 | Ouvrière qualifiée de l'alimentation, du travail sur bois, de l'habillement"),
                (603, "6.3 | Ouvrière qualifiée de la métallurgie, de la construction mécanique, de l'imprimerie, de l'électricité et de l'électronique"),
                (604, "6.4 | Conductrice de machines et d'installations fixes, ouvrière qualifiée de l'assemblage"),
                (605, '6.5 | Conductrice de véhicules et de matériels et engins mobiles'),
            ]),
            ('7 | Profession salariée peu qualifiée', [
                (701, '7.1 | Personnelle de service et employée de commerce'),
                (702, '7.2 | Ouvrière peu qualifiée et manœuvre'),
                (703, '7.3 | Agente d\'entretien'),
                (704, '7.4 | Ouvrière agricole'),
            ]),
            ('9 | Hors marché du travail', [
                (902, '9.2 | Personne handicapée inapte de moins de 65 ans'),
                (903, '9.3 | Chômeuse non classée dans une autre catégorie'),
                (904, '9.4 | Autre personne hors du marché du travail'),
            ]),
            ('13 | Non réponse', [
                (1300, '13 | Je ne sais pas ou ne peux pas répondre'),
            ]),
        ]

        conj_csp_grouped_choices = [
            ('1 | Cadre dirigeant·e', [
                (101, "1.1 | Chef·fe d'entreprise, hors hôtellerie, restauration, commerce"),
                (102, "1.2 | Chef·fe d'entreprise, hôtellerie, restauration, commerce"),
                (103, "1.3 | Cadre dirigeant·e salarié·e, hors hôtellerie, restauration, commerce"),
                (104, "1.4 | Cadre dirigeant·e ou gérant·e, hôtellerie, restauration, commerce"),
            ]),
            ('2 | Profession intellectuelle ou scientifique', [
                (201, "2.1 | Ingénieur·e ou spécialiste des sciences, des techniques, des TIC"),
                (202, "2.2 | Médecin ou professionnel·le de santé"),
                (203, "2.3 | Cadre administratif·ve, financier·ère ou commercial·e"),
                (204, "2.4 | Professionnel·le de la justice, des sciences sociales ou de la culture"),
                (205, "2.5 | Enseignant·e ou professionnel·le de l’enseignement"),
            ]),
            ('3 | Profession intermédiaire salariée', [
                (301, "3.1 | Profession intermédiaire des sciences, des techniques, des TIC"),
                (302, "3.2 | Profession intermédiaire salariée de la santé"),
                (303, "3.3 | Profession intermédiaire de finance, vente et administration"),
                (304, "3.4 | Profession intermédiaire des services juridiques, des services sociaux et assimilés"),
                (305, "3.5 | Sous-officier·ère des forces armées"),
            ]),
            ('4 | Petit·e entrepreneur·e (non-salarié·e)', [
                (401, '4.1 | Exploitant·e agricole'),
                (402, '4.2 | Commerçant·e et assimilé·e'),
                (403, '4.3 | Artisan·e'),
            ]),
            ('5 | Employé·e qualifié·e', [
                (501, '5.1 | Employé·e de bureau et assimilé·e'),
                (502, '5.2 | Employé·e de réception, guichetier·ère et assimilé·e'),
                (503, '5.3 | Aide-soignant·e, garde d’enfant et aide-enseignant·e'),
                (504, '5.4 | Personnel des services de protection, de sécurité et des armées'),
            ]),
            ('6 | Ouvrier·ère qualifié·e salarié·e', [
                (601, '6.1 | Ouvrier·ère qualifié·e de la construction, sauf électricien·ne'),
                (602, "6.2 | Ouvrier·ère qualifié·e de l'alimentation, du travail sur bois, de l'habillement"),
                (603, "6.3 | Ouvrier·ère qualifié·e de la métallurgie, de la construction mécanique, de l'imprimerie, de l'électricité et de l'électronique"),
                (604, "6.4 | Conducteur·rice de machines et d'installations fixes, ouvrier·ère qualifié·e de l'assemblage"),
                (605, '6.5 | Conducteur·rice de véhicules et de matériels et engins mobiles'),
            ]),
            ('7 | Profession salariée peu qualifiée', [
                (701, '7.1 | Personnel de service et employé·e de commerce'),
                (702, '7.2 | Ouvrier·ère peu qualifié·e et manœuvre'),
                (703, '7.3 | Agent·e d’entretien'),
                (704, '7.4 | Ouvrier·ère agricole'),
            ]),
            ('9 | Hors marché du travail', [
                (902, '9.2 | Personne handicapée inapte de moins de 65 ans'),
                (903, '9.3 | Chômeur·se non classé·e dans une autre catégorie'),
                (904, '9.4 | Autre personne hors du marché du travail'),
            ]),
            ('13 | Non réponse', [
                (1300, '13 | Je ne sais pas ou ne peux pas répondre'),
            ]),
        ]

        field = self.fields.get('pere_csp')
        if field:
            field.choices = [('', 'Sélectionnez...')] + pere_csp_grouped_choices

        field = self.fields.get('mere_csp')
        if field:
            field.choices = [('', 'Sélectionnez...')] + mere_csp_grouped_choices

        field = self.fields.get('conj_csp')
        if field:
            field.choices = [('', 'Sélectionnez...')] + conj_csp_grouped_choices

        # Retire les choix vides automatiques qui s'affichent comme "---------".
        # Les champs select conservent un libellé explicite "Sélectionnez..." quand nécessaire.
        fields_without_blank_choice = [
            'perception_financiere',
            'perception_risque_pauvrete',
            'position_subjective_classe',
            'perception_mobilite',
            'discri_presence',
            'sante_generale',
            'det_1', 'det_2', 'det_3', 'det_4', 'det_5',
        ]
        for field_name in fields_without_blank_choice:
            field = self.fields.get(field_name)
            if not field:
                continue
            field.choices = [
                (value, label)
                for value, label in field.choices
                if value not in (None, '')
            ]

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

        # Conditions pour les enfants cohabitants.
        has_children_at_home = cleaned_data.get('composition_logement_enfants')
        nb_enfants_cohabitants = cleaned_data.get('nb_enfants_cohabitants')
        nb_enfants_moins14 = cleaned_data.get('nb_enfants_moins14')

        if has_children_at_home:
            if nb_enfants_cohabitants is None:
                self.add_error('nb_enfants_cohabitants', "Ce champ est requis si vous vivez avec un enfant ou des enfants.")

            if nb_enfants_moins14 is None:
                self.add_error('nb_enfants_moins14', "Ce champ est requis si vous vivez avec un enfant ou des enfants.")

            if nb_enfants_cohabitants is not None and nb_enfants_cohabitants >= 20:
                self.add_error('nb_enfants_cohabitants', "La valeur doit être inférieure à 20.")

            if nb_enfants_moins14 is not None and nb_enfants_moins14 >= 20:
                self.add_error('nb_enfants_moins14', "La valeur doit être inférieure à 20.")

            if (
                nb_enfants_cohabitants is not None
                and nb_enfants_moins14 is not None
                and nb_enfants_moins14 > nb_enfants_cohabitants
            ):
                self.add_error('nb_enfants_moins14', "Le nombre d'enfants de moins de 14 ans doit être inférieur ou égal au nombre total d'enfants cohabitants.")
        else:
            cleaned_data['nb_enfants_cohabitants'] = None
            cleaned_data['nb_enfants_moins14'] = None

        # Questions conjoint uniquement si la personne vit avec son/sa conjoint·e.
        if not cleaned_data.get('composition_logement_conjoint'):
            cleaned_data['conj_niv_diplome'] = None
            cleaned_data['conj_csp'] = None

        # Questions discrimination détaillées uniquement si discrimination présente.
        discri_present = cleaned_data.get('discri_presence') in (1, 2)
        discri_reason_fields = [
            'discri_age', 'discri_genre', 'discri_sante_physique', 'discri_sante_mentale',
            'discri_couleur_peau', 'discri_origine_nationalite', 'discri_situation_familiale',
            'discri_orientation_sexuelle', 'discri_autre'
        ]
        discri_context_fields = [
            'discri_contexte_emploi', 'discri_contexte_logement', 'discri_contexte_travail',
            'discri_contexte_education', 'discri_contexte_sante', 'discri_contexte_famille',
            'discri_contexte_autre'
        ]

        if not discri_present:
            for field_name in discri_reason_fields + discri_context_fields:
                cleaned_data[field_name] = False
            cleaned_data['discri_autre_precision'] = ''
        else:
            if not any(cleaned_data.get(name) for name in discri_reason_fields):
                self.add_error('discri_presence', 'Veuillez sélectionner au moins une raison de discrimination.')
            if not any(cleaned_data.get(name) for name in discri_context_fields):
                self.add_error('discri_presence', 'Veuillez sélectionner au moins un contexte de discrimination.')
            if cleaned_data.get('discri_autre') and not (cleaned_data.get('discri_autre_precision') or '').strip():
                self.add_error('discri_autre_precision', 'Précisez la raison "autre".')
            if not cleaned_data.get('discri_autre'):
                cleaned_data['discri_autre_precision'] = ''

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

            # Ruse temporaire: conserver toute la logique de délai (7 jours)
            # mais rendre les nouveaux inscrits immédiatement éligibles,
            # sans toucher la vraie date de création du profil.
            profil.created_at_trick = timezone.now() - timezone.timedelta(days=8)
            profil.save(update_fields=['created_at_trick'])
        
        return user