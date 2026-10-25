from collections import Counter

from django.utils import timezone

from .models import Reve


PALIERS = (
    {"niveau": 1, "cle": "courbe", "libelle": "Courbe"},
    {"niveau": 2, "cle": "tonalite", "libelle": "Tonalité"},
    {"niveau": 3, "cle": "emotions", "libelle": "Émotions"},
    {"niveau": 4, "cle": "temps", "libelle": "Temps"},
    {"niveau": 5, "cle": "themes", "libelle": "Thèmes"},
    {"niveau": 6, "cle": "profil", "libelle": "Profil"},
    {"niveau": 7, "cle": "rapport", "libelle": "Rapport"},
)
PROFILS = {
    "oublieux": {
        "name": "Oublieux·se", "color": "#98a2b3",
        "hook": "Profil marqué par un rappel onirique faible : les récits sont courts et fragmentaires.",
        "paragraph": "Vos récits sont brefs et contiennent peu d'éléments narratifs : une image isolée, une sensation ou une émotion résiduelle. Ce schéma correspond à un rappel onirique partiel, phénomène très répandu qui varie notamment selon les conditions de réveil, la qualité du sommeil et l'attention portée aux rêves. La faible densité de thèmes et de personnages limite l'analyse détaillée, mais les éléments rapportés sont en général ceux qui présentent la plus forte saillance émotionnelle.",
        "traits": ("Rappel fragmentaire", "Faible densité narrative", "Saillance émotionnelle"),
    },
    "nostalgique": {
        "name": "Nostalgique", "color": "#ca8aa0",
        "hook": "Profil orienté vers le passé, avec une tonalité émotionnelle plutôt positive.",
        "paragraph": "Vos récits mobilisent fréquemment la mémoire autobiographique : lieux familiers, personnes de l'entourage passé, situations déjà vécues. Les figures relationnelles (famille, amis, anciens proches) y occupent une place importante, ce qui rejoint l'hypothèse de continuité, selon laquelle le rêve reprend les préoccupations et les liens sociaux de la vie éveillée. La valence émotionnelle dominante est positive ou apaisée, et le niveau de détail descriptif est élevé.",
        "traits": ("Orientation vers le passé", "Forte présence relationnelle", "Valence positive"),
    },
    "melancolique": {
        "name": "Mélancolique", "color": "#3245bd",
        "hook": "Profil orienté vers le passé, avec une tonalité émotionnelle négative ou ambivalente.",
        "paragraph": "Comme dans le profil nostalgique, vos récits s'appuient sur la mémoire autobiographique (enfance, anciens lieux de vie, personnes perdues de vue), mais la valence émotionnelle y est plus souvent négative ou mixte : tristesse, regret, sentiment de perte. Les thèmes liés aux ruptures biographiques (séparations, déménagements, deuils) y sont plus fréquents. Les récits sont longs, détaillés, et les émotions y sont souvent nommées explicitement.",
        "traits": ("Mémoire autobiographique", "Valence négative ou mixte", "Thèmes de la perte"),
    },
    "explorateur": {
        "name": "Explorateur·rice", "color": "#3e8e9c",
        "hook": "Profil orienté vers le présent et la nouveauté, avec une forte dynamique narrative.",
        "paragraph": "Vos récits comportent de nombreux changements de lieu, d'action et de situation, et peu de références au passé. Les cadres inconnus ou inhabituels y sont plus fréquents que les cadres familiers. Les émotions rapportées sont associées à l'action (surprise, curiosité, excitation) plutôt qu'à la réflexion, ce qui se traduit par une proportion élevée de verbes d'action et de transitions entre les scènes.",
        "traits": ("Cadres inhabituels", "Forte densité d'actions", "Émotions liées à l'action"),
    },
    "vigilant": {
        "name": "Vigilant·e", "color": "#d4a017",
        "hook": "Profil orienté vers le présent et l'avenir, centré sur les préoccupations et l'anticipation.",
        "paragraph": "Vos récits reprennent fréquemment des enjeux de la vie éveillée : travail, études, obligations, échéances à venir. On y relève une part élevée de situations de contrainte (retard, obstacle, épreuve, évaluation), que certaines théories rapprochent d'une fonction de simulation ou de préparation aux situations menaçantes et sociales. Les émotions relèvent souvent de l'appréhension ou du stress, mais sont décrites de façon factuelle et précise.",
        "traits": ("Continuité avec la vie éveillée", "Situations de contrainte", "Anticipation"),
    },
    "equilibriste": {
        "name": "Équilibriste", "color": "#6b9de1",
        "hook": "Profil sans orientation temporelle dominante, avec une forte diversité thématique.",
        "paragraph": "Vos récits se répartissent de manière relativement homogène entre passé, présent et futur, sans registre dominant. La diversité des thèmes, des lieux et des personnages est élevée, et les émotions rapportées sont variées, parfois combinées au sein d'un même récit. Ce profil correspond moins à une tendance marquée qu'à une distribution équilibrée des différents indicateurs.",
        "traits": ("Pas d'orientation dominante", "Diversité thématique", "Émotions mixtes"),
    },
}

TEMPS_SCORES = {
    "temps_passe_lointain": -2,
    "temps_passe_recent": -1,
    "temps_veille": 0,
    "temps_futur_proche": 1,
    "temps_futur_lointain": 2,
}


def _dates(reves):
    return {
        reve.date or timezone.localtime(reve.created_at).date()
        for reve in reves
        if reve.date or reve.created_at
    }


def get_nuits(user):
    return sorted(_dates(Reve.objects.filter(user=user)))


def get_nuits_avec_souvenir(user):
    return sorted(_dates(Reve.objects.filter(user=user, existence_souvenir=True)))


def get_palier(user):
    return min(len(get_nuits(user)), 7)


def calculer_profil(user):
    reves = list(Reve.objects.filter(user=user, existence_souvenir=True))
    remembered_nights = len(_dates(reves))
    temps_values = [
        TEMPS_SCORES[field]
        for reve in reves
        for field in TEMPS_SCORES
        if getattr(reve, field)
    ]
    tonalite_values = {
        "tres_positif": 1, "positif": 1, "neutre": 0,
        "mauvais": -1, "cauchemar": -1,
    }
    tonalites = [
        tonalite_values[reve.type_reve]
        for reve in reves
        if reve.type_reve in tonalite_values
    ]
    score_temps = sum(temps_values) / len(temps_values) if temps_values else 0
    score_tonalite = sum(tonalites) / len(tonalites) if tonalites else 0
    emotion_counter = Counter(
        emotion.libelle
        for reve in reves
        for emotion in (*reve.emotions_reve.all(), *reve.emotions_custom.all())
    )
    theme_counter = Counter(
        theme.strip()
        for reve in reves
        for theme in (reve.elements_reve or [])
        if isinstance(theme, str) and theme.strip()
    )
    dominant_time = next(
        (
            label for field, label in (
                ("temps_passe_lointain", "le passé lointain"),
                ("temps_passe_recent", "le passé récent"),
                ("temps_veille", "les événements récents"),
                ("temps_futur_proche", "le futur proche"),
                ("temps_futur_lointain", "le futur lointain"),
            )
            if sum(getattr(reve, field) for reve in reves)
            == max(
                (sum(getattr(reve, candidate) for reve in reves)
                 for candidate in TEMPS_SCORES),
                default=0,
            )
        ),
        None,
    )

    if remembered_nights < 3:
        code = "oublieux"
    elif abs(score_temps) < 0.3 and abs(score_tonalite) < 0.15:
        code = "equilibriste"
    elif score_temps < 0 and score_tonalite >= 0:
        code = "nostalgique"
    elif score_temps < 0:
        code = "melancolique"
    elif score_tonalite >= 0:
        code = "explorateur"
    else:
        code = "vigilant"

    profile = PROFILS[code]
    observations = profile["paragraph"]
    if theme_counter:
        observations += f" Le thème qui revient le plus dans vos récits est « {theme_counter.most_common(1)[0][0]} »."
    if emotion_counter:
        observations += f" L'émotion la plus souvent nommée est {emotion_counter.most_common(1)[0][0].lower()}."
    if dominant_time:
        observations += f" La temporalité la plus présente est {dominant_time}."
    return {
        "code": code,
        "name": profile["name"],
        "color": profile["color"],
        "hook": profile["hook"],
        "paragraph": observations,
        "traits": profile["traits"],
        "score_temps": round(score_temps, 2),
        "score_tonalite": round(score_tonalite, 2),
        "remembered_nights": remembered_nights,
    }
