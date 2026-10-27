"""Configuration and category mappings for the survey follow-up dashboard."""

from .models import Questionnaire


SURVEY_TARGET = 1500

QUOTA_TARGETS = {
    'genre': {'Femmes': 750, 'Hommes': 750},
    'age': {'18-20 ans': 375, '21-24 ans': 500, '25-29 ans': 625},
    'genre_age': {
        'Femmes 18-20 ans': 188,
        'Femmes 21-24 ans': 250,
        'Femmes 25-29 ans': 313,
        'Hommes 18-20 ans': 188,
        'Hommes 21-24 ans': 250,
        'Hommes 25-29 ans': 313,
    },
    'situation': {
        'En études': 302,
        'Études + emploi': 171,
        'En emploi': 747,
        'Au chômage': 125,
        'Inactif (hors études)': 160,
        'Étudiants (études + cumul)': 473,
        'Non-étudiants': 1032,
    },
    'habitat': {'Île-de-France': 270, 'Hors Île-de-France': 1230},
    'diplome': {'Au plus le brevet': 69, 'Bac+2 ou plus': 332},
}


GENRE_FEMME = Questionnaire.GenreChoices.FEMME
GENRE_HOMME = Questionnaire.GenreChoices.HOMME
HABITAT_PARIS_REGION = Questionnaire.HabitatChoices.PARIS_REGION
TRAVAIL_EN_EMPLOI = Questionnaire.TravailChoices.EN_EMPLOI
TRAVAIL_EN_ETUDES = Questionnaire.TravailChoices.EN_ETUDES
TRAVAIL_AU_CHOMAGE = Questionnaire.TravailChoices.AU_CHOMAGE
AT_MOST_BREVET = {
    Questionnaire.DiplomeChoices.AUCUN,
    Questionnaire.DiplomeChoices.CEP,
    Questionnaire.DiplomeChoices.BEPC,
}
BAC_PLUS_DEUX = {
    Questionnaire.DiplomeChoices.BAC_2,
    Questionnaire.DiplomeChoices.BAC_3_4,
    Questionnaire.DiplomeChoices.BAC_5,
    Questionnaire.DiplomeChoices.DOCTORAT,
}

# The questionnaire stores the current main situation in one choice. The only
# additional employment signal is "a déjà travaillé 6 mois"; it is therefore
# used as the available proxy for the "études + emploi" quota.
