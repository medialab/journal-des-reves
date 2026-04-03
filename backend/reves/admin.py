import csv
from collections import Counter
from datetime import timedelta

from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.db import models
from django.db.models import Count
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import (
    Notification,
    Profil,
    Questionnaire,
    Reve,
    ReveElementCustom,
    ReveEmotion,
    ReveEmotionCustom,
    ReveImageModalite,
)


# Profil Admin
class ProfilAdmin(ModelAdmin):
    list_display = ['user', 'consent_data_processing', 'consent_date']
    search_fields = ['user__username', 'user__email']
    list_filter = ['consent_data_processing', 'consent_date']


class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False
    fk_name = 'user'
    extra = 0
    verbose_name_plural = 'Profil associé'
    fields = (
        'email',
        'consent_data_processing',
        'consent_password_account',
        'consent_quote_expressions',
        'consent_date',
        'welcome_email_sent',
        'created_at',
    )
    readonly_fields = ('created_at',)


class GroupBulkUpdateForm(forms.Form):
    mode = forms.ChoiceField(
        label='Mode de mise à jour',
        choices=(
            ('replace', 'Remplacer les groupes'),
            ('add', 'Ajouter aux groupes existants'),
            ('remove', 'Retirer des groupes existants'),
        ),
        initial='replace',
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Groupes',
    )


class UserAdminForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by('name'),
        required=False,
        label='Groupes',
        widget=forms.CheckboxSelectMultiple,
        help_text='Cochez les groupes à attribuer à cet utilisateur.',
    )

    class Meta:
        model = User
        fields = '__all__'


class UserAdmin(DjangoUserAdmin):
    form = UserAdminForm
    inlines = (ProfilInline,)
    actions = ('bulk_update_groups', 'delete_selected', 'quick_delete_users')
    actions_on_top = True
    actions_on_bottom = True
    filter_horizontal = ('user_permissions',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        (
            'Groupes',
            {
                'description': 'Affectez les groupes de façon simple en cochant les options nécessaires.',
                'fields': ('groups',),
            },
        ),
        (
            'Permissions avancees',
            {
                'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions'),
                'classes': ('collapse',),
            },
        ),
        ('Dates importantes', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'groups_display',
        'is_staff',
        'is_active',
        'is_superuser',
        'last_login',
        'date_joined',
        'delete_link',
    )
    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        'groups',
        'date_joined',
        'last_login',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'groups__name',
        'profil__email',
    )
    list_select_related = ()

    @admin.display(description='Groupes')
    def groups_display(self, obj):
        values = [group.name for group in obj.groups.all()]
        return ', '.join(values) if values else '—'

    @admin.display(description='Action')
    def delete_link(self, obj):
        delete_url = reverse('admin:auth_user_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="display:inline-block;padding:0.2rem 0.55rem;border-radius:999px;border:1px solid #dc2626;color:#dc2626;font-weight:600;text-decoration:none;">Supprimer</a>',
            delete_url,
        )

    @admin.action(description='Modifier les groupes (choix multiples)')
    def bulk_update_groups(self, request, queryset):
        if 'apply' in request.POST:
            form = GroupBulkUpdateForm(request.POST)
            if form.is_valid():
                selected_groups = list(form.cleaned_data['groups'])
                mode = form.cleaned_data['mode']
                updated_count = 0

                for user in queryset:
                    if mode == 'replace':
                        user.groups.set(selected_groups)
                    elif mode == 'add':
                        user.groups.add(*selected_groups)
                    elif mode == 'remove':
                        user.groups.remove(*selected_groups)
                    updated_count += 1

                self.message_user(
                    request,
                    f'Groupes mis à jour pour {updated_count} utilisateur(s).',
                    level=messages.SUCCESS,
                )
                return None
        else:
            form = GroupBulkUpdateForm()

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'users': queryset,
            'form': form,
            'action_name': 'bulk_update_groups',
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'title': 'Modifier les groupes des utilisateurs sélectionnés',
        }
        return TemplateResponse(request, 'admin/auth/user/group_bulk_update.html', context)

    @admin.action(description='Suppression rapide des utilisateurs sélectionnés')
    def quick_delete_users(self, request, queryset):
        # Éviter l'auto-suppression de l'admin connecté.
        skipped_self = queryset.filter(pk=request.user.pk).count()
        target_qs = queryset.exclude(pk=request.user.pk)
        target_count = target_qs.count()

        if target_count == 0:
            self.message_user(
                request,
                'Aucun utilisateur supprimé (vous ne pouvez pas supprimer votre propre compte depuis cette action).',
                level=messages.WARNING,
            )
            return

        try:
            target_qs.delete()
        except Exception as exc:
            self.message_user(
                request,
                f'Échec de suppression: {exc}',
                level=messages.ERROR,
            )
            return

        suffix = f' ({skipped_self} compte admin ignoré)' if skipped_self else ''
        self.message_user(
            request,
            f'{target_count} utilisateur(s) supprimé(s) avec succès{suffix}.',
            level=messages.SUCCESS,
        )

class GroupAdmin(DjangoGroupAdmin):
    list_display = ('name', 'users_count', 'permissions_count')
    search_fields = ('name',)

    @admin.display(description='Utilisateurs')
    def users_count(self, obj):
        return obj.user_set.count()

    @admin.display(description='Permissions')
    def permissions_count(self, obj):
        return obj.permissions.count()


# Reve Admin
class ReveAdmin(ModelAdmin):
    change_list_template = 'admin/reves/reve/data_change_list.html'
    list_display = [
        'dreamer',
        'date',
        'existence_souvenir',
        'type_reve',
        'etendue_reve',
        'sens',
        'images_modalites_display',
        'emotion_display',
        'elements_reve_display',
        'temporalite_display',
        'transcription_ready',
        'audio_present',
        'transcription_excerpt',
        'created_at',
    ]
    search_fields = ['user__username', 'profil__user__username', 'transcription', 'commentaire_libre']
    list_filter = [
        'date',
        'existence_souvenir',
        'type_reve',
        'etendue_reve',
        'sens',
        'transcription_ready',
        'temps_passe_lointain',
        'temps_passe_recent',
        'temps_veille',
        'temps_futur_proche',
        'temps_futur_lointain',
        'temps_difficile',
    ]
    readonly_fields = ['created_at', 'date']
    actions = ['export_selected_as_csv']
    list_per_page = 25
    date_hierarchy = 'date'
    fieldsets = [
        ("Informations", {"fields": ["user", "profil", "date", "created_at", "existence_souvenir", "audio", "transcription_ready"]}),
        ("Transcription", {"fields": ["transcription"]}),
        ("Rêve - Métadonnées", {
            "fields": ["type_reve", "etendue_reve", "sens", "images_modalites"],
        }),
        ("Rêve - Émotions", {
            "fields": ["emotions_reve", "emotions_custom"],
        }),
        ("Rêve - Contexte et commentaire", {
            "fields": ["elements_reve", "temps_passe_lointain", "temps_passe_recent", "temps_veille", "temps_futur_proche", "temps_futur_lointain", "temps_difficile", "commentaire_libre"],
        }),
    ]

    temps_field_specs = [
        ('temps_passe_lointain', 'Passé lointain'),
        ('temps_passe_recent', 'Passé récent'),
        ('temps_veille', 'Veille'),
        ('temps_futur_proche', 'Futur proche'),
        ('temps_futur_lointain', 'Futur lointain'),
        ('temps_difficile', 'Difficile à dire'),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'profil', 'profil__user').prefetch_related(
            'images_modalites',
            'emotions_reve',
            'emotions_custom',
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'dashboard/',
                self.admin_site.admin_view(self.dashboard_view),
                name='reves_reve_dashboard',
            ),
            path(
                'export-csv/',
                self.admin_site.admin_view(self.export_all_as_csv_view),
                name='reves_reve_export_csv',
            ),
        ]
        return custom_urls + urls

    @admin.display(description='Participant', ordering='profil__user__username')
    def dreamer(self, obj):
        if obj.profil_id and obj.profil.user_id:
            return obj.profil.user.username
        if obj.user_id:
            return obj.user.username
        return '—'

    @admin.display(description='Audio', boolean=True)
    def audio_present(self, obj):
        return bool(obj.audio)

    @admin.display(description='Modalités images')
    def images_modalites_display(self, obj):
        values = [item.libelle for item in obj.images_modalites.all()]
        return ', '.join(values) if values else '—'

    @admin.display(description='Émotions')
    def emotion_display(self, obj):
        values = [item.libelle for item in obj.emotion]
        return ', '.join(values) if values else '—'

    @admin.display(description='Éléments')
    def elements_reve_display(self, obj):
        return ', '.join(obj.elements_reve) if obj.elements_reve else '—'

    @admin.display(description='Temporalité')
    def temporalite_display(self, obj):
        values = [label for field_name, label in self.temps_field_specs if getattr(obj, field_name)]
        return ', '.join(values) if values else '—'

    @admin.display(description='Transcription')
    def transcription_excerpt(self, obj):
        if not obj.transcription:
            return '—'
        excerpt = obj.transcription.strip().replace('\n', ' ')
        if len(excerpt) > 100:
            excerpt = f'{excerpt[:97]}...'
        return excerpt

    def dashboard_view(self, request):
        changelist = self.get_changelist_instance(request)
        queryset = changelist.queryset
        query_string = request.GET.urlencode()
        data_url = reverse('admin:reves_reve_changelist')
        csv_url = reverse('admin:reves_reve_export_csv')
        if query_string:
            data_url = f'{data_url}?{query_string}'
            csv_url = f'{csv_url}?{query_string}'

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Dashboard rêves',
            'dashboard': self.build_dashboard_context(queryset),
            'data_url': data_url,
            'csv_export_url': csv_url,
        }
        return TemplateResponse(request, 'admin/reves/reve/dashboard.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data') and response.context_data.get('cl'):
            response.context_data['csv_export_url'] = f"{reverse('admin:reves_reve_export_csv')}?{request.GET.urlencode()}"
            response.context_data['dashboard_url'] = f"{reverse('admin:reves_reve_dashboard')}?{request.GET.urlencode()}"

        return response

    def build_dashboard_context(self, queryset):
        total_count = queryset.count()
        total_profiles = queryset.values('profil_id').distinct().count()
        memory_count = queryset.filter(existence_souvenir=True).count()
        transcription_ready_count = queryset.filter(transcription_ready=True).count()
        audio_count = queryset.exclude(audio='').exclude(audio__isnull=True).count()
        avg_reves_per_profile = round(total_count / total_profiles, 1) if total_profiles else 0

        return {
            'cards': [
                {'label': 'Rêves visibles', 'value': total_count, 'help_text': 'Rêves selon les filtres actifs'},
                {'label': 'Participants actifs', 'value': total_profiles, 'help_text': 'Profils distincts avec au moins un rêve'},
                {'label': 'Souvenirs de rêve', 'value': memory_count, 'help_text': f'{round(memory_count / total_count * 100, 1) if total_count else 0}% des entrées'},
                {'label': 'Transcriptions prêtes', 'value': transcription_ready_count, 'help_text': f'{round(transcription_ready_count / total_count * 100, 1) if total_count else 0}% des rêves'},
                {'label': 'Rêves par participant', 'value': avg_reves_per_profile, 'help_text': f'{audio_count} entrées avec audio'},
            ],
            'recent_series': self.build_recent_series(queryset),
            'valence': self.build_valence_context(queryset),
            'top_emotions': self.build_top_emotions(queryset),
            'top_themes': self.build_top_themes(queryset),
            'temps_stats': self.build_temps_stats(queryset),
            'type_distribution': self.build_choice_distribution(queryset, 'type_reve', 'Tonalité déclarée'),
            'modality_distribution': self.build_modalities_distribution(queryset),
        }

    def build_recent_series(self, queryset):
        # Agrégation hebdomadaire (12 semaines glissantes, semaine ISO lundi->dimanche)
        today = timezone.localdate()
        current_week_start = today - timedelta(days=today.weekday())
        weeks = []
        for offset in range(11, -1, -1):
            week_start = current_week_start - timedelta(weeks=offset)
            week_end = week_start + timedelta(days=6)
            weeks.append((week_start, week_end))

        counts = []
        for week_start, week_end in weeks:
            count = queryset.filter(date__gte=week_start, date__lte=week_end).count()
            counts.append(count)

        max_count = max(counts, default=0)
        series = []
        for (week_start, _week_end), count in zip(weeks, counts):
            height = int((count / max_count) * 100) if max_count else 0
            series.append({
                'label': f"S{week_start.isocalendar().week:02d}",
                'count': count,
                'height': max(height, 10) if count else 0,
            })
        return series

    def build_valence_context(self, queryset):
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
        for dream_type in queryset.exclude(type_reve__isnull=True).exclude(type_reve='').values_list('type_reve', flat=True):
            bucket = valence_map.get(dream_type)
            if bucket:
                valence_counter[bucket] += 1
            score = type_scores.get(dream_type)
            if score:
                weighted_sum += score

        total = sum(valence_counter.values())
        cursor_pct = round((weighted_sum / total - 1) / 4 * 100, 1) if total else None
        segments = []
        for key, label in [('positif', 'Positif'), ('neutre', 'Neutre'), ('negatif', 'Négatif')]:
            count = valence_counter[key]
            percentage = round((count / total) * 100, 1) if total else 0
            segments.append({'label': label, 'count': count, 'percentage': percentage})
        return {'total': total, 'cursor_pct': cursor_pct, 'segments': segments}

    def build_top_emotions(self, queryset):
        counter = Counter()
        for reve in queryset:
            counter.update([item.libelle for item in reve.emotion])
        return self.counter_to_distribution(counter, limit=8)

    def build_top_themes(self, queryset):
        counter = Counter()
        for elements in queryset.exclude(elements_reve=[]).values_list('elements_reve', flat=True):
            if not elements:
                continue
            for raw_value in elements:
                cleaned = (raw_value or '').strip()
                if cleaned:
                    counter[cleaned] += 1
        return self.counter_to_distribution(counter, limit=10)

    def build_temps_stats(self, queryset):
        total = queryset.count()
        items = []
        for field_name, label in self.temps_field_specs:
            count = queryset.filter(**{field_name: True}).count()
            percentage = round((count / total) * 100, 1) if total else 0
            items.append({'label': label, 'count': count, 'percentage': percentage})
        return items

    def build_choice_distribution(self, queryset, field_name, label):
        field = Reve._meta.get_field(field_name)
        choices_map = dict(field.flatchoices)
        rows = queryset.exclude(**{f'{field_name}__isnull': True})
        if isinstance(field, (models.CharField, models.TextField)):
            rows = rows.exclude(**{field_name: ''})
        rows = rows.values(field_name).annotate(count=Count('id')).order_by('-count')
        total = sum(row['count'] for row in rows)
        items = []
        for row in rows:
            raw_value = row[field_name]
            items.append({
                'label': choices_map.get(raw_value, raw_value),
                'count': row['count'],
                'percentage': round((row['count'] / total) * 100, 1) if total else 0,
            })
        return {'label': label, 'items': items}

    def build_modalities_distribution(self, queryset):
        counter = Counter()
        for reve in queryset:
            counter.update([item.libelle for item in reve.images_modalites.all()])
        return {'label': 'Modalités visuelles', 'items': self.counter_to_distribution(counter, limit=8)}

    def counter_to_distribution(self, counter, limit=10):
        """Convert a Counter to a list of distribution items"""
        total = sum(counter.values())
        items = []
        for label, count in counter.most_common(limit):
            percentage = round((count / total) * 100, 1) if total else 0
            items.append({'label': label, 'count': count, 'percentage': percentage})
        return items

    def export_queryset_as_csv(self, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="reves.csv"'

        writer = csv.writer(response)
        model_fields = list(Reve._meta.fields)
        header = ['username', 'email']
        for field in model_fields:
            header.append(field.name)
            if field.choices:
                header.append(f'{field.name}_label')
        header.extend([
            'images_modalites_labels',
            'emotion_labels',
            'elements_reve_labels',
            'temporalite_labels',
        ])
        writer.writerow(header)

        for reve in queryset:
            row = [
                reve.profil.user.username if reve.profil_id and reve.profil.user_id else '',
                reve.profil.email if reve.profil_id else '',
            ]
            for field in model_fields:
                value = getattr(reve, field.name)
                if field.name == 'user':
                    export_value = reve.user.username if reve.user_id else ''
                elif field.name == 'profil':
                    export_value = reve.profil_id
                elif field.name == 'audio':
                    export_value = value.name if value else ''
                else:
                    export_value = value
                row.append(export_value)
                if field.choices:
                    row.append(getattr(reve, f'get_{field.name}_display')() if value not in [None, ''] else '')
            row.extend([
                ' | '.join(item.libelle for item in reve.images_modalites.all()),
                ' | '.join(item.libelle for item in reve.emotion),
                ' | '.join(reve.elements_reve or []),
                ' | '.join(label for field_name, label in self.temps_field_specs if getattr(reve, field_name)),
            ])
            writer.writerow(row)

        return response

    @admin.action(description='Exporter la sélection en CSV')
    def export_selected_as_csv(self, request, queryset):
        return self.export_queryset_as_csv(queryset.order_by('id'))

    def export_all_as_csv_view(self, request):
        queryset = self.get_changelist_instance(request).queryset.order_by('id')
        return self.export_queryset_as_csv(queryset)


# Questionnaire Admin
class QuestionnaireAdmin(ModelAdmin):
    change_list_template = 'admin/reves/questionnaire/data_change_list.html'
    list_display = [
        'user',
        'profil',
        'completion_badge',
        'created_at',
        'completed_at',
        'completion_duration_display',
        'frequency',
        'sleep_quality',
    ]
    search_fields = ['user__username', 'profil__user__username']
    list_filter = ['is_completed', 'created_at', 'completed_at', 'frequency', 'sleep_quality']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'completion_duration_seconds']
    actions = ['export_selected_as_csv']

    key_field_specs = [
        ('genre', 'Genre'),
        ('niv_diplome', 'Diplôme'),
        ('lieu_naissance', 'Lieu de naissance'),
        ('discri_presence', 'Discriminations'),
        ('sante_generale', 'Santé générale'),
        ('heure_coucher', 'Heure de coucher'),
        ('temps_du_reve', 'Temporalité du rêve'),
    ]

    distribution_specs = [
        ('sleep_quality', 'Qualité du sommeil'),
        ('frequency', 'Fréquence de rappel des rêves'),
        ('discri_presence', 'Traitements inégalitaires / discriminations'),
        ('genre', 'Genre'),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'profil', 'profil__user')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'dashboard/',
                self.admin_site.admin_view(self.dashboard_view),
                name='reves_questionnaire_dashboard',
            ),
            path(
                'export-csv/',
                self.admin_site.admin_view(self.export_all_as_csv_view),
                name='reves_questionnaire_export_csv',
            ),
        ]
        return custom_urls + urls

    @admin.display(description='Statut', ordering='is_completed')
    def completion_badge(self, obj):
        label = 'Complété' if obj.is_completed else 'Brouillon'
        background = '#e7f6ec' if obj.is_completed else '#fff3cd'
        color = '#146c2e' if obj.is_completed else '#8a6d1d'
        if obj.is_completed:
            return format_html(
                '<span style="display:inline-block;padding:0.2rem 0.55rem;border-radius:999px;background:{};color:{};font-weight:600;">{}</span>',
                background,
                color,
                label,
            )
        return format_html(
            '<span style="display:inline-block;padding:0.2rem 0.55rem;border-radius:999px;background:{};color:{};font-weight:600;">{}</span>',
            background,
            color,
            label,
        )

    @admin.display(description='Durée')
    def completion_duration_display(self, obj):
        seconds = obj.estimated_completion_duration_seconds
        if seconds is None:
            return '—'
        minutes, remaining_seconds = divmod(seconds, 60)
        if minutes:
            return f'{minutes} min {remaining_seconds:02d}s'
        return f'{remaining_seconds}s'

    def dashboard_view(self, request):
        changelist = self.get_changelist_instance(request)
        queryset = changelist.queryset
        query_string = request.GET.urlencode()
        data_url = reverse('admin:reves_questionnaire_changelist')
        csv_url = reverse('admin:reves_questionnaire_export_csv')
        if query_string:
            data_url = f'{data_url}?{query_string}'
            csv_url = f'{csv_url}?{query_string}'

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Dashboard questionnaires',
            'dashboard': self.build_dashboard_context(queryset),
            'data_url': data_url,
            'csv_export_url': csv_url,
        }
        return TemplateResponse(request, 'admin/reves/questionnaire/dashboard.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data') and response.context_data.get('cl'):
            response.context_data['csv_export_url'] = f"{reverse('admin:reves_questionnaire_export_csv')}?{request.GET.urlencode()}"
            response.context_data['dashboard_url'] = f"{reverse('admin:reves_questionnaire_dashboard')}?{request.GET.urlencode()}"

        return response

    def build_dashboard_context(self, queryset):
        now = timezone.now()
        eligible_since = now - timedelta(days=7)
        eligible_profiles_count = Profil.objects.filter(
            user__is_active=True,
            created_at__lte=eligible_since,
        ).count()
        completed_profiles_count = Questionnaire.objects.filter(is_completed=True).values('profil_id').distinct().count()

        total_count = queryset.count()
        completed_count = queryset.filter(is_completed=True).count()
        draft_count = max(0, total_count - completed_count)

        completion_rate = round((completed_count / total_count) * 100, 1) if total_count else 0
        eligible_completion_rate = round((completed_profiles_count / eligible_profiles_count) * 100, 1) if eligible_profiles_count else 0

        durations = []
        for questionnaire in queryset.filter(is_completed=True):
            seconds = questionnaire.estimated_completion_duration_seconds
            if seconds is not None:
                durations.append(seconds)
        average_duration_seconds = round(sum(durations) / len(durations)) if durations else None

        recent_series = self.build_recent_series(queryset)
        distributions = [self.build_distribution(queryset, field_name, label) for field_name, label in self.distribution_specs]
        key_field_completion = [self.build_field_completion(queryset, field_name, label) for field_name, label in self.key_field_specs]

        return {
            'cards': [
                {'label': 'Réponses visibles', 'value': total_count, 'help_text': 'Questionnaires selon les filtres actuels'},
                {'label': 'Questionnaires complétés', 'value': completed_count, 'help_text': f'{completion_rate}% de la sélection'},
                {'label': 'Brouillons en base', 'value': draft_count, 'help_text': 'Sauvegardes partielles non soumises'},
                {
                    'label': 'Taux de complétion global',
                    'value': f'{eligible_completion_rate}%',
                    'help_text': f'{completed_profiles_count} profils complétés sur {eligible_profiles_count} profils éligibles',
                },
                {
                    'label': 'Temps moyen de passation',
                    'value': self.format_duration(average_duration_seconds),
                    'help_text': 'Durée totale persistée à la soumission finale',
                },
            ],
            'recent_series': recent_series,
            'distributions': [distribution for distribution in distributions if distribution['items']],
            'key_field_completion': key_field_completion,
        }

    def build_recent_series(self, queryset):
        today = timezone.localdate()
        start_day = today - timedelta(days=13)
        completed_counts = {
            item['completed_at__date']: item['count']
            for item in queryset.filter(
                is_completed=True,
                completed_at__date__gte=start_day,
            ).values('completed_at__date').annotate(count=Count('id'))
        }
        max_count = max(completed_counts.values(), default=0)
        series = []
        for day_offset in range(14):
            day = start_day + timedelta(days=day_offset)
            count = completed_counts.get(day, 0)
            height = int((count / max_count) * 100) if max_count else 0
            series.append(
                {
                    'label': day.strftime('%d/%m'),
                    'count': count,
                    'height': max(height, 8) if count else 0,
                }
            )
        return series

    def build_distribution(self, queryset, field_name, label):
        field = Questionnaire._meta.get_field(field_name)
        choices_map = dict(field.flatchoices)
        rows = queryset.exclude(**{f'{field_name}__isnull': True}).values(field_name).annotate(count=Count('id')).order_by('-count')
        total = sum(row['count'] for row in rows)
        items = []
        for row in rows:
            raw_value = row[field_name]
            display = choices_map.get(raw_value, raw_value)
            percentage = round((row['count'] / total) * 100, 1) if total else 0
            items.append({'label': display, 'count': row['count'], 'percentage': percentage})
        return {'label': label, 'items': items, 'total': total}

    def build_field_completion(self, queryset, field_name, label):
        total = queryset.count()
        field = Questionnaire._meta.get_field(field_name)
        filled_queryset = queryset.exclude(**{f'{field_name}__isnull': True})
        if isinstance(field, (models.CharField, models.TextField)):
            filled_queryset = filled_queryset.exclude(**{field_name: ''})
        filled_count = filled_queryset.count()
        percentage = round((filled_count / total) * 100, 1) if total else 0
        return {'label': label, 'count': filled_count, 'percentage': percentage}

    def format_duration(self, seconds):
        if seconds is None:
            return '—'
        minutes, remaining_seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f'{hours} h {minutes:02d} min'
        if minutes:
            return f'{minutes} min {remaining_seconds:02d}s'
        return f'{remaining_seconds}s'

    def export_queryset_as_csv(self, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="questionnaires.csv"'

        writer = csv.writer(response)
        model_fields = list(Questionnaire._meta.fields)

        header = ['username', 'email']
        for field in model_fields:
            header.append(field.name)
            if field.choices:
                header.append(f'{field.name}_label')
        header.extend(['duree_som_minutes', 'deficit_som_minutes'])
        writer.writerow(header)

        for questionnaire in queryset.select_related('profil__user', 'user'):
            row = [
                questionnaire.profil.user.username if questionnaire.profil_id and questionnaire.profil.user_id else '',
                questionnaire.profil.email if questionnaire.profil_id else '',
            ]
            for field in model_fields:
                value = getattr(questionnaire, field.name)
                if field.name == 'user':
                    export_value = questionnaire.user.username if questionnaire.user_id else ''
                elif field.name == 'profil':
                    export_value = questionnaire.profil_id
                else:
                    export_value = value
                row.append(export_value)
                if field.choices:
                    row.append(getattr(questionnaire, f'get_{field.name}_display')())
            row.extend([questionnaire.duree_som, questionnaire.deficit_som])
            writer.writerow(row)

        return response

    @admin.action(description='Exporter la sélection en CSV')
    def export_selected_as_csv(self, request, queryset):
        return self.export_queryset_as_csv(queryset.order_by('id'))

    def export_all_as_csv_view(self, request):
        queryset = self.get_changelist_instance(request).queryset.order_by('id')
        return self.export_queryset_as_csv(queryset)


# Notification Admin
class NotificationAdmin(ModelAdmin):
    list_display = ['profil', 'notification_type', 'title', 'is_read', 'created_at']
    search_fields = ['profil__user__username', 'title']
    list_filter = ['notification_type', 'is_read', 'created_at']
    readonly_fields = ['created_at', 'read_at']
    fieldsets = [
        ("Information", {"fields": ["profil", "notification_type", "title", "message"]}),
        ("Statut", {"fields": ["is_read", "created_at", "read_at"]}),
    ]


class ReveEmotionAdmin(ModelAdmin):
    list_display = ['libelle', 'emoji', 'ordre']
    search_fields = ['libelle', 'emoji']
    ordering = ['ordre', 'libelle']


class ReveEmotionCustomAdmin(ModelAdmin):
    list_display = ['libelle', 'profil', 'created_at']
    search_fields = ['libelle', 'profil__user__username', 'profil__email']
    list_filter = ['created_at']
    autocomplete_fields = ['profil']


class ReveImageModaliteAdmin(ModelAdmin):
    list_display = ['libelle', 'ordre']
    search_fields = ['libelle']
    ordering = ['ordre', 'libelle']


class ReveElementCustomAdmin(ModelAdmin):
    list_display = ['libelle', 'profil', 'created_at']
    search_fields = ['libelle', 'profil__user__username', 'profil__email']
    list_filter = ['created_at']
    autocomplete_fields = ['profil']


admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Profil, ProfilAdmin)
admin.site.register(Reve, ReveAdmin)
admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(ReveEmotion, ReveEmotionAdmin)
admin.site.register(ReveEmotionCustom, ReveEmotionCustomAdmin)
admin.site.register(ReveImageModalite, ReveImageModaliteAdmin)
admin.site.register(ReveElementCustom, ReveElementCustomAdmin)