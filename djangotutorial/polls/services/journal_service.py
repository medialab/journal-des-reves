from django.db.models import Count
from django.db.models.functions import TruncMonth
from ..models import Reve


def get_journal_data(profil):

    reves = Reve.objects.filter(profil=profil)

    total = reves.count()

    # ===== STATISTIQUES POUR LES GRAPHIQUES =====
    
    # 1. Émotions - Agréger pour un camembert
    emotions_data = (
        reves
        .values("emotions_reve__libelle")
        .exclude(emotions_reve__isnull=True)
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    # Formater pour le graphique
    emotions_labels = [
        emotion['emotions_reve__libelle'] 
        for emotion in emotions_data
    ]
    emotions_counts = [
        emotion['count'] 
        for emotion in emotions_data
    ]

    # 2. Étendue du rêve - Bar chart
    etendue_data = (
        reves
        .values("etendue_reve")
        .exclude(etendue_reve__isnull=True)
        .annotate(count=Count("id"))
        .order_by("etendue_reve")
    )
    
    # Formater pour le graphique
    etendue_labels = [
        dict(Reve.EtenduReve.choices).get(item['etendue_reve'], f"Type {item['etendue_reve']}")
        for item in etendue_data
    ]
    etendue_counts = [
        item['count'] 
        for item in etendue_data
    ]

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
        "emotions_labels": emotions_labels,
        "emotions_counts": emotions_counts,
        "etendue_labels": etendue_labels,
        "etendue_counts": etendue_counts,
        "stats_mensuelles": stats_mensuelles,
    }