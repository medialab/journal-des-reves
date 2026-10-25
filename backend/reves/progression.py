from collections import Counter

from django.utils import timezone

from .models import Reve


PALIERS = (
    {"niveau": 1, "cle": "courbe", "libelle": "Courbe"},
    {"niveau": 2, "cle": "tonalite", "libelle": "Tonalité"},
    {"niveau": 3, "cle": "emotions", "libelle": "Émotions"},
    {"niveau": 4, "cle": "temps", "libelle": "Temps"},
    {"niveau": 5, "cle": "themes", "libelle": "Thèmes"},
    {"niveau": 6, "cle": "rapport", "libelle": "Rapport"},
    {"niveau": 7, "cle": "profil", "libelle": "Profil"},
)

PROFILS = {
    "oublieux": {
        "name": "Oublieux·se", "color": "#98a2b3",
        "hook": "Vos rêves passent parfois comme des lucioles : brefs, présents, puis déjà loin.",
        "paragraph": "Vous racontez surtout les fragments qui restent au réveil : une image, une sensation ou une émotion. Les détails et les thèmes se font plus discrets, mais chaque souvenir compte. Votre récit va à l'essentiel, avec une place importante laissée à ce qui revient malgré l'oubli.",
        "traits": ("Fragments marquants", "Récits à l'essentiel", "Émotions-souvenirs"),
    },
    "nostalgique": {
        "name": "Nostalgique", "color": "#ca8aa0",
        "hook": "Vos nuits savent retrouver les chemins doux qui ramènent vers hier.",
        "paragraph": "Vos rêves aiment revenir vers le passé, les lieux familiers et les personnes qui ont compté. Vous racontez les scènes avec une attention particulière aux détails qui donnent une couleur au souvenir. Une émotion douce accompagne souvent le récit, sans l'enfermer dans une seule lecture.",
        "traits": ("Souvenirs du passé", "Détails affectifs", "Récits tout en nuances"),
    },
    "melancolique": {
        "name": "Mélancolique", "color": "#3245bd",
        "hook": "Vos rêves aiment revenir en arrière, là où les souvenirs gardent encore une résonance.",
        "paragraph": "Vos récits revisitent souvent le passé : lieux d'enfance, personnes perdues de vue ou scènes que vous pensiez oubliées. Vous prêtez attention à ce qui a compté et aux émotions qui accompagnent ces retours. Votre manière de raconter laisse une place aux nuances et aux silences, comme une mémoire qui se déploie doucement.",
        "traits": ("Souvenirs d'enfance fréquents", "Récits riches en émotions", "Attention aux détails"),
    },
    "explorateur": {
        "name": "Explorateur·rice", "color": "#3e8e9c",
        "hook": "Vos rêves ouvrent des portes vers des situations nouvelles, avec un élan curieux.",
        "paragraph": "Vos récits se tournent volontiers vers le présent et ce qui pourrait arriver ensuite. Vous explorez des lieux, des situations et des possibilités variées, en racontant les changements qui traversent la scène. Les émotions sont souvent mêlées à l'action, ce qui donne à vos histoires un mouvement très vivant.",
        "traits": ("Goût des situations nouvelles", "Récits en mouvement", "Curiosité narrative"),
    },
    "vigilant": {
        "name": "Vigilant·e", "color": "#d4a017",
        "hook": "Vos nuits observent le présent et l'avenir avec une attention fine.",
        "paragraph": "Vous racontez des rêves ancrés dans les préoccupations du moment et les événements à venir. Votre récit repère les signaux, les obstacles et les décisions qui donnent du relief à la scène. Les émotions peuvent être intenses, mais votre façon de les décrire reste attentive et concrète.",
        "traits": ("Attention au présent", "Anticipation de l'avenir", "Récits précis"),
    },
    "equilibriste": {
        "name": "Équilibriste", "color": "#6b9de1",
        "hook": "Vos rêves circulent librement entre souvenirs, présent et futurs possibles.",
        "paragraph": "Vos récits passent d'une époque à l'autre sans s'installer durablement dans un seul registre. Vous associez des thèmes, des lieux et des émotions variés avec une grande souplesse. Votre style de récit garde une tonalité nuancée, capable de faire coexister plusieurs impressions dans une même histoire.",
        "traits": ("Registres variés", "Émotions nuancées", "Récits souples"),
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
