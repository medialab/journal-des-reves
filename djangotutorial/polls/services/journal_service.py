from collections import Counter
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

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

    # 3. Souvenirs de rêves cette semaine
    week_start = timezone.localdate() - timedelta(days=6)
    weekly_dream_count = reves.filter(date__gte=week_start, existence_souvenir=True).count()

    # Courbe hebdomadaire (1 point = nombre de rêves sur une semaine lundi-dimanche)
    weekly_curve_labels = []
    weekly_curve_counts = []
    memory_dates = list(
        reves.filter(existence_souvenir=True)
        .order_by('date')
        .values_list('date', flat=True)
    )

    if memory_dates:
        week_counter = Counter()
        for dream_date in memory_dates:
            monday = dream_date - timedelta(days=dream_date.weekday())
            week_counter[monday] += 1

        first_monday = memory_dates[0] - timedelta(days=memory_dates[0].weekday())
        last_monday = memory_dates[-1] - timedelta(days=memory_dates[-1].weekday())

        cursor = first_monday
        while cursor <= last_monday:
            sunday = cursor + timedelta(days=6)
            weekly_curve_labels.append(f"{cursor.strftime('%d/%m')}-{sunday.strftime('%d/%m')}")
            weekly_curve_counts.append(week_counter.get(cursor, 0))
            cursor += timedelta(days=7)

    # 4. Tonalité des rêves
    valence_map = {
        Reve.TypeReve.TRES_POSITIF: 'positif',
        Reve.TypeReve.POSITIF: 'positif',
        Reve.TypeReve.NEUTRE: 'neutre',
        Reve.TypeReve.MAUVAIS: 'negatif',
        Reve.TypeReve.CAUCHEMAR: 'negatif',
    }
    type_scores = {
        Reve.TypeReve.TRES_POSITIF: 1,
        Reve.TypeReve.POSITIF: 2,
        Reve.TypeReve.NEUTRE: 3,
        Reve.TypeReve.MAUVAIS: 4,
        Reve.TypeReve.CAUCHEMAR: 5,
    }
    valence_counter = Counter({'positif': 0, 'neutre': 0, 'negatif': 0})
    weighted_sum = 0
    for dream_type in reves.exclude(type_reve__isnull=True).exclude(type_reve='').values_list('type_reve', flat=True):
        bucket = valence_map.get(dream_type)
        if bucket:
            valence_counter[bucket] += 1
        score = type_scores.get(dream_type)
        if score:
            weighted_sum += score

    valence_total = sum(valence_counter.values())
    # Position du curseur sur l'axe très positif (0%) → cauchemar (100%)
    valence_cursor_pct = round((weighted_sum / valence_total - 1) / 4 * 100, 1) if valence_total else None
    valence_segments = []
    for key, label, icon in [
        ('positif', 'Positif', '🙂'),
        ('neutre', 'Neutre', '😐'),
        ('negatif', 'Négatif', '☹️'),
    ]:
        count = valence_counter[key]
        percentage = round((count / valence_total) * 100, 1) if valence_total else 0
        valence_segments.append({
            'key': key,
            'label': label,
            'icon': icon,
            'count': count,
            'percentage': percentage,
        })

    # 5. Espace thématique
    theme_counter = Counter()
    for element_list in reves.exclude(elements_reve=[]).values_list('elements_reve', flat=True):
        if not element_list:
            continue
        for raw_theme in element_list:
            theme = (raw_theme or '').strip()
            if theme:
                theme_counter[theme] += 1

    top_themes_raw = theme_counter.most_common(8)
    max_theme_count = top_themes_raw[0][1] if top_themes_raw else 0
    top_themes = []
    for index, (theme, count) in enumerate(top_themes_raw):
        ratio = (count / max_theme_count) if max_theme_count else 0
        top_themes.append({
            'theme': theme,
            'count': count,
            'size': round(58 + ratio * 76),
            'font_size': round(11 + ratio * 7),
            'offset_x': ((index * 37 + 13) % 21) - 10,
            'offset_y': ((index * 23 + 7) % 17) - 8,
            'opacity': round(0.16 + ratio * 0.48, 2),
            'border_opacity': round(0.28 + ratio * 0.42, 2),
        })

    # 6. Le temps du rêve
    _TEMPS_FIELDS = [
        ('temps_passe_lointain', 'Passé lointain'),
        ('temps_passe_recent', 'Passé récent'),
        ('temps_veille', 'Veille'),
        ('temps_futur_proche', 'Futur proche'),
        ('temps_futur_lointain', 'Futur lointain'),
        ('temps_difficile', 'Difficile à dire'),
    ]
    temps_stats = []
    for field, label in _TEMPS_FIELDS:
        count = reves.filter(**{field: True}).count()
        percentage = round(count / total * 100, 1) if total else 0
        temps_stats.append({'key': field, 'label': label, 'count': count, 'percentage': percentage})
    temps_total = sum(item['count'] for item in temps_stats)

    return {
        "reves": reves.order_by("-date"),
        "total_reves": total,
        "emotions_labels": emotions_labels,
        "emotions_counts": emotions_counts,
        "etendue_labels": etendue_labels,
        "etendue_counts": etendue_counts,
        "stats_mensuelles": stats_mensuelles,
        "weekly_dream_count": weekly_dream_count,
            "weekly_curve_labels": weekly_curve_labels,
            "weekly_curve_counts": weekly_curve_counts,
        "valence_total": valence_total,
        "valence_cursor_pct": valence_cursor_pct,
        "valence_segments": valence_segments,
        "top_themes": top_themes,
        "temps_total": temps_total,
        "temps_stats": temps_stats,
    }