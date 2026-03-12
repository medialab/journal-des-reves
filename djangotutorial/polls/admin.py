from django.contrib import admin

from .models import Profil, Reve, Questionnaire, Notification, ReveElementCustom


# Profil Admin
class ProfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'consent_data_processing', 'consent_date']
    search_fields = ['user__username', 'user__email']
    list_filter = ['consent_data_processing', 'consent_date']


# Reve Admin
class ReveAdmin(admin.ModelAdmin):
    list_display = ['user', 'profil', 'date', 'type_reve', 'transcription_ready', 'audio', 'transcription', 'created_at']
    search_fields = ['user__username', 'profil__user__username']
    list_filter = ['date', 'type_reve', 'transcription_ready']
    readonly_fields = ['created_at', 'date']
    fieldsets = [
        ("Informations", {"fields": ["user", "profil", "date", "audio"]}),
        ("Transcription", {"fields": ["transcription", "transcription_ready"]}),
        ("Rêve - Métadonnées", {
            "fields": ["type_reve", "etendue_reve", "sens"],
            "classes": ["collapse"]
        }),
        ("Rêve - Émotions et Tags", {
            "fields": ["emotions_reve", "emotions_custom", "tags"],
            "classes": ["collapse"]
        }),
        ("Rêve - Contexte et commentaire", {
            "fields": ["elements_reve", "temps_reve", "commentaire_libre"],
            "classes": ["collapse"]
        }),
    ]


# Questionnaire Admin
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ['user', 'profil', 'created_at', 'frequency', 'sleep_quality']
    search_fields = ['user__username', 'profil__user__username']
    list_filter = ['created_at', 'frequency', 'sleep_quality']
    readonly_fields = ['created_at', 'updated_at']


# Notification Admin
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['profil', 'notification_type', 'title', 'is_read', 'created_at']
    search_fields = ['profil__user__username', 'title']
    list_filter = ['notification_type', 'is_read', 'created_at']
    readonly_fields = ['created_at', 'read_at']
    fieldsets = [
        ("Information", {"fields": ["profil", "notification_type", "title", "message"]}),
        ("Statut", {"fields": ["is_read", "created_at", "read_at"]}),
    ]


admin.site.register(Profil, ProfilAdmin)
admin.site.register(Reve, ReveAdmin)
admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(ReveElementCustom)