from collections import Counter

from django.utils import timezone

from .models import Reve


PALIERS = (
    {"niveau": 1, "cle": "courbe", "libelle": "Courbe", "detail": "La courbe hebdomadaire se débloque après votre première nuit."},
    {"niveau": 2, "cle": "tonalite", "libelle": "Tonalité", "detail": "Découvrez la tonalité émotionnelle de vos rêves après deux nuits."},
    {"niveau": 3, "cle": "emotions", "libelle": "Émotions", "detail": "Analysez les émotions nommées dans vos récits après trois nuits."},
    {"niveau": 4, "cle": "temps", "libelle": "Temps", "detail": "Observez les repères temporels de vos rêves après quatre nuits."},
    {"niveau": 5, "cle": "themes", "libelle": "Thèmes", "detail": "Explorez les thèmes qui reviennent dans vos récits après cinq nuits."},
    {"niveau": 6, "cle": "profil", "libelle": "Profil", "detail": "Votre profil de rêveur est établi après six nuits."},
    {"niveau": 7, "cle": "rapport", "libelle": "Rapport", "detail": "Le rapport complet est préparé à la fin de l'enquête."},
)
PROFILS = {
    "oublieux": {
        "name": "Les Oublieux·ses", "color": "#98a2b3",
        "hook": "Vous vous souvenez de peu de vos rêves.",
        "paragraph": "Sur la semaine, la plupart de vos nuits se sont terminées sans souvenir de rêve, et vos récits sont courts.",
        "traits": ("Peu de souvenirs", "Récits courts"),
    },
    "intermittent": {
        "name": "Les Intermittent·es", "color": "#6b9de1",
        "hook": "Vous vous souvenez d'une partie de vos rêves.",
        "paragraph": "Sur la semaine, vous vous êtes souvenu·e de vos rêves certaines nuits mais pas toutes, avec des récits de longueur moyenne.",
        "traits": ("Souvenirs certaines nuits", "Récits de longueur moyenne"),
    },
    "grand_reveur": {
        "name": "Les Grand·es rêveur·euses", "color": "#3245bd",
        "hook": "Vous vous souvenez de beaucoup de vos rêves.",
        "paragraph": "Sur la semaine, vous vous êtes souvenu·e de vos rêves la plupart des nuits, et vos récits sont longs.",
        "traits": ("Beaucoup de souvenirs", "Récits longs"),
    },
}

RAPPEL_ONIRIQUE = (
    "Tout le monde rêve chaque nuit : ce qui varie d'une personne à l'autre, c'est le souvenir. "
    "Le cerveau endormi ne mémorise pas les rêves : pour qu'un rêve soit retenu, il faut se réveiller "
    "pendant ou juste après, environ deux minutes. Le rappel onirique dépend donc surtout des éveils "
    "au cours de la nuit. Les personnes qui se souviennent souvent de leurs rêves se réveillent deux fois "
    "plus souvent la nuit que les autres, et cumulent en moyenne une quinzaine de minutes d'éveil nocturne "
    "contre cinq. Plus la nuit est longue, plus elle compte de cycles de sommeil, et plus les occasions "
    "de se réveiller et de retenir un rêve sont nombreuses."
)

TAUX_OUBLIEUX = 0.4
TAUX_GRAND_REVEUR = 0.7
MOTS_GRAND_REVEUR = 80


def _dates(reves):
    return {_nuit(reve) for reve in reves if reve.date or reve.created_at}


def _nuit(reve):
    return reve.date or timezone.localtime(reve.created_at).date()


def get_nuits(user):
    return sorted(_dates(Reve.objects.filter(user=user)))


def get_nuits_avec_souvenir(user):
    return sorted(_dates(Reve.objects.filter(user=user, existence_souvenir=True)))


def get_palier(user):
    return min(len(get_nuits(user)), 7)


def calculer_profil(user):
    reves = list(Reve.objects.filter(user=user))
    nuits = _dates(reves)
    souvenirs = [reve for reve in reves if reve.existence_souvenir]
    nuits_souvenir = _dates(souvenirs)

    mots_par_nuit = Counter()
    for reve in souvenirs:
        mots_par_nuit[_nuit(reve)] += len((reve.transcription or "").split())

    nb_nuits = len(nuits)
    nb_souvenirs = len(nuits_souvenir)
    taux = nb_souvenirs / nb_nuits if nb_nuits else 0
    longueur_moyenne = sum(mots_par_nuit.values()) / nb_souvenirs if nb_souvenirs else 0

    if taux < TAUX_OUBLIEUX:
        code = "oublieux"
    elif taux >= TAUX_GRAND_REVEUR and longueur_moyenne >= MOTS_GRAND_REVEUR:
        code = "grand_reveur"
    else:
        code = "intermittent"

    profile = PROFILS[code]
    observations = profile["paragraph"]
    if nb_nuits:
        observations += (
            f" Sur vos {nb_nuits} nuits renseignées, vous vous êtes souvenu·e de vos rêves "
            f"{nb_souvenirs} fois"
        )
        if nb_souvenirs:
            observations += f", avec des récits de {round(longueur_moyenne)} mots en moyenne"
        observations += "."
    observations += " " + RAPPEL_ONIRIQUE
    return {
        "code": code,
        "name": profile["name"],
        "color": profile["color"],
        "hook": profile["hook"],
        "paragraph": observations,
        "traits": profile["traits"],
        "nuits": nb_nuits,
        "remembered_nights": nb_souvenirs,
        "taux_souvenir": round(taux, 2),
        "longueur_moyenne": round(longueur_moyenne),
    }
