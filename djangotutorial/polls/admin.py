from django.contrib import admin

from .models import Choice, Question, Profil, Reve, Emotion, EmotionCustom, Tag, Questionnaire


class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]


# Profil Admin
class ProfilAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'genre', 'birth_year', 'email']
    search_fields = ['name', 'user__username', 'email']
    list_filter = ['genre', 'birth_year']


# Emotion Admin
class EmotionAdmin(admin.ModelAdmin):
    list_display = ['emoji', 'libelle', 'ordre']
    ordering = ['ordre', 'libelle']


# Emotion Custom Admin
class EmotionCustomAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'profil', 'created_at']
    search_fields = ['libelle', 'profil__name']
    list_filter = ['profil', 'created_at']


# Tag Admin
class TagAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'profil', 'couleur', 'created_at']
    search_fields = ['libelle', 'profil__name']
    list_filter = ['profil', 'created_at']


# Reve Admin
class ReveAdmin(admin.ModelAdmin):
    list_display = ['profil', 'date', 'type_reve', 'transcription_ready', 'created_at']
    search_fields = ['profil__name']
    list_filter = ['date', 'type_reve', 'transcription_ready']
    readonly_fields = ['created_at', 'date']
    fieldsets = [
        ("Informations", {"fields": ["profil", "date", "audio"]}),
        ("Transcription", {"fields": ["transcription", "transcription_ready"]}),
        ("Rêve - Métadonnées", {
            "fields": ["type_reve", "etendue_reve", "sens"],
            "classes": ["collapse"]
        }),
        ("Rêve - Émotions et Tags", {
            "fields": ["emotions_reve", "emotions_custom", "tags"],
            "classes": ["collapse"]
        }),
    ]


# Questionnaire Admin
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ['profil', 'created_at', 'frequency', 'sleep_quality']
    search_fields = ['profil__name']
    list_filter = ['created_at', 'frequency', 'sleep_quality']
    readonly_fields = ['created_at', 'updated_at']


admin.site.register(Question, QuestionAdmin)
admin.site.register(Profil, ProfilAdmin)
admin.site.register(Reve, ReveAdmin)
admin.site.register(Emotion, EmotionAdmin)
admin.site.register(EmotionCustom, EmotionCustomAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Questionnaire, QuestionnaireAdmin)