from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth
from ..models import Reve


def get_journal_data(profil):

    reves = Reve.objects.filter(profil=profil)

    total = reves.count()

    moyenne_intensite = reves.aggregate(
        Avg("intensite")
    )["intensite__avg"]

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
        "moyenne_intensite": moyenne_intensite,
        "stats_mensuelles": stats_mensuelles,
    }