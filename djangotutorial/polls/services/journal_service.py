from django.db.models import Count
from django.db.models.functions import TruncMonth
from ..models import Reve


def get_journal_data(profil):

    reves = Reve.objects.filter(profil=profil)

    total = reves.count()

    tags_stats = (
        reves
        .values("tags__libelle")
        .exclude(tags__isnull=True)
        .distinct()
    )

    emotions_stats = (
        reves
        .values("emotions_reve__libelle")
        .exclude(emotions_reve__isnull=True)
        .distinct()
    )

    stats_mensuelles = (
        reves
        .annotate(mois=TruncMonth("date"))
        .values("mois")
        .annotate(total=Count("id"))
        .order_by("mois")
    )

    return {
        "reves": reves.order_by("-date"),
        "total_reves": total,
        "tags_stats": list(tags_stats),
        "emotions_stats": list(emotions_stats),
        "stats_mensuelles": stats_mensuelles,
    }