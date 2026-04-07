from django.db.models import F
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, JsonResponse, FileResponse, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.views import generic, View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from django.core.cache import cache
import uuid
import os
import mimetypes
import json
import csv
import time
import wave

from .models import Reve, Profil, Questionnaire, ReveEmotion, ReveEmotionCustom, ReveElementCustom, ReveImageModalite, Notification
from .services.journal_service import get_journal_data
from .services.transcription_service import start_transcription_async
from .forms import ReveForm, QuestionnaireForm, SignUpForm


# Security/abuse protection constants
MAX_AUDIO_DURATION_SECONDS = 15 * 60
MAX_AUDIO_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_AUDIO_UPLOADS_PER_DAY = 7
MAX_QUESTIONNAIRE_SUBMISSIONS = 5

UPLOAD_RATE_LIMIT = 10
UPLOAD_RATE_WINDOW_SECONDS = 60
EXPORT_RATE_LIMIT = 5
EXPORT_RATE_WINDOW_SECONDS = 5 * 60
NOTIFICATIONS_MUTATION_RATE_LIMIT = 20
NOTIFICATIONS_MUTATION_RATE_WINDOW_SECONDS = 60
NOTIFICATIONS_READ_RATE_LIMIT = 60
NOTIFICATIONS_READ_RATE_WINDOW_SECONDS = 60

MAX_RATE_LIMIT_BACKOFF_SECONDS = 300
QUESTIONNAIRE_MIN_SECTION_DURATION_SECONDS = 1
QUESTIONNAIRE_MAX_SECTION_DURATION_SECONDS = 30 * 60
QUESTIONNAIRE_DUPLICATE_SUBMIT_WINDOW_SECONDS = 15

ALLOWED_AUDIO_EXTENSIONS = {'.wav', '.mp4a', '.m4a', '.mp4', '.webm'}
ALLOWED_AUDIO_CONTENT_TYPES = {
    'audio/wav',
    'audio/x-wav',
    'audio/wave',
    'audio/mp4',
    'audio/x-m4a',
    'audio/m4a',
    'audio/webm',
    'video/webm',
    'video/mp4',
}


def _rate_limit(user_id, scope, limit, window_seconds):
    """Return (is_allowed, retry_after_seconds) using cache-based fixed window + backoff."""
    now = int(time.time())
    block_key = f"rl:block:{scope}:{user_id}"
    blocked_until = cache.get(block_key)

    if blocked_until and blocked_until > now:
        return False, blocked_until - now

    bucket = now // window_seconds
    count_key = f"rl:count:{scope}:{user_id}:{bucket}"

    try:
        count = cache.incr(count_key)
    except ValueError:
        cache.set(count_key, 1, timeout=window_seconds + 5)
        count = 1

    if count > limit:
        over_limit = count - limit
        backoff_seconds = min(MAX_RATE_LIMIT_BACKOFF_SECONDS, 2 ** min(over_limit + 1, 8))
        cache.set(block_key, now + backoff_seconds, timeout=backoff_seconds)
        return False, backoff_seconds

    return True, 0


def _rate_limited_json_response(retry_after, message):
    response = JsonResponse({
        'success': False,
        'message': message,
        'retry_after_seconds': retry_after,
    }, status=429)
    response['Retry-After'] = str(retry_after)
    return response


def _safe_csv_cell(value):
    if value is None:
        return ''
    text = str(value)
    if text and text[0] in ('=', '+', '-', '@'):
        return "'" + text
    return text


def _validate_audio_upload(audio_file):
    """Return error message string if invalid, otherwise None."""
    if audio_file.size > MAX_AUDIO_FILE_SIZE_BYTES:
        return "Fichier audio trop volumineux (max 25 MB)."

    extension = os.path.splitext(audio_file.name or '')[1].lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        return "Format audio non autorisé. Formats acceptés: WAV, M4A/MP4A, MP4, WEBM."

    content_type = (audio_file.content_type or '').lower().strip()
    if content_type and content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
        return "Type MIME audio non autorisé."

    # Validation de durée robuste pour WAV. Pour les autres formats,
    # la limite de taille + MIME/extension est appliquée ici.
    if extension == '.wav':
        try:
            audio_file.seek(0)
            with wave.open(audio_file, 'rb') as wav_file:
                frame_rate = wav_file.getframerate()
                frame_count = wav_file.getnframes()
                if frame_rate <= 0:
                    return "Fichier audio invalide (fréquence d'échantillonnage)."
                duration_seconds = frame_count / float(frame_rate)
        except (wave.Error, EOFError):
            return "Fichier audio invalide ou non conforme au format WAV."
        finally:
            try:
                audio_file.seek(0)
            except Exception:
                pass

        if duration_seconds > MAX_AUDIO_DURATION_SECONDS:
            return "Durée audio trop longue (max 15 minutes)."

    return None


# Helper functions
def add_questionnaire_context(context, profil):
    """Ajouter les informations de questionnaire au contexte"""
    has_questionnaire = profil.has_completed_questionnaire()
    questionnaire_required = profil.must_complete_questionnaire_for_extended_access()
    context['has_questionnaire'] = has_questionnaire
    context['questionnaire_required'] = questionnaire_required
    return context


class ProfilView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.error(request, "Profil non trouve. Veuillez contacter l'administrateur.")
            return HttpResponseRedirect(reverse("reves:index"))

        if profil.must_complete_questionnaire_for_extended_access():
            messages.warning(
                request,
                "Veuillez completer le questionnaire pour acceder aux statistiques du profil."
            )
            return HttpResponseRedirect(reverse("reves:questionnaire"))

        journal_data = get_journal_data(profil)

        context = {
            "profil": profil,
            "user": request.user,
            **journal_data
        }
        
        # Ajouter les infos questionnaire
        context = add_questionnaire_context(context, profil)

        return render(request, "reves/profil.html", context)
    
    def post(self, request):
        """Gérer la mise à jour du profil"""
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=400)
        
        import json
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({
                'success': False,
                'message': 'Données invalides'
            }, status=400)
        
        # Mettre à jour les champs autorisés
        if 'email' in data:
            profil.email = data['email']
        
        try:
            profil.save()
            messages.success(request, "Profil mis à jour avec succès !")
            return JsonResponse({
                'success': True,
                'message': 'Profil mis à jour'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            }, status=400)

class DescriptionView(View):
    template_name = "reves/description.html"
    
    def get(self, request):
        return render(request, self.template_name)



class EnregistrerView(LoginRequiredMixin, View):
    """
    Vue pour enregistrer un nouveau rêve avec audio et métadonnées
    La transcription est traitée de manière asynchrone avec Whisper
    """

    def _get_recording_mode(self, user):
        """Déterminer le mode d'enregistrement selon le groupe de l'utilisateur"""
        if user.groups.filter(name='text_only').exists():
            return 'text_only'
        return 'audio_recording'  # Mode par défaut

    def get(self, request):
        """Afficher la page d'enregistrement"""
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.error(request, "Profil utilisateur introuvable")
            return HttpResponseRedirect(reverse("reves:index"))

        if profil.must_complete_questionnaire_for_extended_access():
            messages.warning(
                request,
                "Veuillez completer le questionnaire avant d'enregistrer un nouveau reve."
            )
            return HttpResponseRedirect(reverse("reves:questionnaire"))
        
        # Récupérer les émotions pour le formulaire
        emotions = ReveEmotion.objects.all().order_by('ordre')
        custom_emotions = ReveEmotionCustom.objects.filter(profil=profil).order_by('libelle')
        custom_elements = ReveElementCustom.objects.filter(profil=profil).order_by('libelle')
        images_modalites = ReveImageModalite.objects.all().order_by('ordre')
        
        context = {
            "title": "Enregistrer un rêve",
            "emotions": emotions,
            "custom_emotions": custom_emotions,
            "custom_elements": custom_elements,
            "images_modalites": images_modalites,
            "recording_mode": self._get_recording_mode(request.user),
        }
        
        # Ajouter les infos questionnaire
        context = add_questionnaire_context(context, profil)
        
        return render(request, "reves/enregistrer.html", context)

    def post(self, request):
        """Gérer l'upload de l'audio et la sauvegarde du rêve"""
        try:
            allowed, retry_after = _rate_limit(
                request.user.id,
                scope='audio_upload',
                limit=UPLOAD_RATE_LIMIT,
                window_seconds=UPLOAD_RATE_WINDOW_SECONDS,
            )
            if not allowed:
                return _rate_limited_json_response(
                    retry_after,
                    "Trop de requêtes d'upload. Veuillez réessayer dans quelques instants.",
                )

            # Vérifier que l'utilisateur a un profil
            try:
                profil = request.user.profil
            except Profil.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil utilisateur introuvable'
                }, status=400)

            if profil.must_complete_questionnaire_for_extended_access():
                return JsonResponse({
                    'success': False,
                    'message': 'Veuillez completer le questionnaire avant d\'enregistrer un nouveau reve.'
                }, status=403)

            recording_mode = self._get_recording_mode(request.user)

            # Récupérer existence_souvenir (par défaut True)
            existence_souvenir_str = request.POST.get('existence_souvenir', '1')
            existence_souvenir = existence_souvenir_str == '1'

            # Si la personne n'a aucun souvenir, créer un rêve vide
            if not existence_souvenir:
                reve = Reve.objects.create(
                    profil=profil,
                    user=request.user,
                    existence_souvenir=False,
                    transcription_ready=True  # Pas de transcription nécessaire
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Entrée enregistrée : aucun souvenir de rêve cette nuit',
                    'reve_id': reve.id,
                })

            # Sinon, traitement normal avec audio
            # Récupérer les données du formulaire
            audio_file = request.FILES.get('audio')
            transcription = request.POST.get('transcription', '').strip()
            type_reve = request.POST.get('type_reve', '').strip()
            etendue_reve = request.POST.get('etendue_reve', '')
            sens = request.POST.get('sens', '')
            emotions_ids = request.POST.getlist('emotions_reve')
            emotions_custom = request.POST.getlist('emotions_custom')
            elements_predefined = request.POST.getlist('elements_reve')
            elements_custom = request.POST.getlist('elements_custom')
            temps_selected = set(request.POST.getlist('temps_reve'))
            commentaire_libre = request.POST.get('commentaire_libre', '').strip()
            images_modalites_ids = request.POST.getlist('images_modalites')

            # Validation
            if recording_mode == 'text_only':
                if not transcription:
                    return JsonResponse({
                        'success': False,
                        'message': 'Veuillez saisir une transcription.'
                    }, status=400)
            else:
                if not audio_file:
                    return JsonResponse({
                        'success': False,
                        'message': 'Aucun fichier audio fourni'
                    }, status=400)

                uploads_today = Reve.objects.filter(
                    profil=profil,
                    date=timezone.localdate(),
                    existence_souvenir=True,
                    audio__isnull=False,
                ).count()
                if uploads_today >= MAX_AUDIO_UPLOADS_PER_DAY:
                    return JsonResponse({
                        'success': False,
                        'message': 'Limite quotidienne atteinte: 7 uploads audio maximum par jour.',
                    }, status=429)

                audio_error = _validate_audio_upload(audio_file)
                if audio_error:
                    return JsonResponse({
                        'success': False,
                        'message': audio_error,
                    }, status=400)

            # Créer le rêve avec le fichier audio
            reve = Reve.objects.create(
                profil=profil,
                user=request.user,
                audio=audio_file if recording_mode == 'audio_recording' else None,
                transcription=transcription if transcription else None,
                type_reve=type_reve if type_reve else None,
                etendue_reve=int(etendue_reve) if etendue_reve else None,
                sens=int(sens) if sens else None,
                temps_passe_lointain='passe_lointain' in temps_selected,
                temps_passe_recent='passe_recent' in temps_selected,
                temps_veille='veille' in temps_selected,
                temps_futur_proche='futur_proche' in temps_selected,
                temps_futur_lointain='futur_lointain' in temps_selected,
                temps_difficile='difficile' in temps_selected,
                commentaire_libre=commentaire_libre if commentaire_libre else None,
                existence_souvenir=True,
                transcription_ready=recording_mode == 'text_only'
            )

            # Ajouter les émotions
            if emotions_ids:
                emotions = ReveEmotion.objects.filter(id__in=emotions_ids)
                reve.emotions_reve.set(emotions)

            # Ajouter les émotions personnalisées
            if emotions_custom:
                custom_objects = []
                for raw_value in emotions_custom:
                    cleaned_value = (raw_value or '').strip()
                    if not cleaned_value:
                        continue
                    existing = ReveEmotionCustom.objects.filter(
                        profil=profil,
                        libelle__iexact=cleaned_value
                    ).first()
                    if existing:
                        custom_objects.append(existing)
                        continue
                    custom_objects.append(ReveEmotionCustom.objects.create(
                        profil=profil,
                        libelle=cleaned_value
                    ))
                if custom_objects:
                    reve.emotions_custom.set(custom_objects)

            # Ajouter les éléments liés au rêve (prédefinis + personnalisés)
            selected_elements = []
            for value in elements_predefined:
                cleaned = (value or '').strip()
                if cleaned and cleaned not in selected_elements:
                    selected_elements.append(cleaned)

            if elements_custom:
                for raw_value in elements_custom:
                    cleaned_value = (raw_value or '').strip()
                    if not cleaned_value:
                        continue
                    existing = ReveElementCustom.objects.filter(
                        profil=profil,
                        libelle__iexact=cleaned_value
                    ).first()
                    if not existing:
                        existing = ReveElementCustom.objects.create(
                            profil=profil,
                            libelle=cleaned_value
                        )
                    if existing.libelle not in selected_elements:
                        selected_elements.append(existing.libelle)

            reve.elements_reve = selected_elements
            reve.save(update_fields=['elements_reve'])

            # Ajouter les modalités d'images
            if images_modalites_ids:
                images_modalites = ReveImageModalite.objects.filter(id__in=images_modalites_ids)
                reve.images_modalites.set(images_modalites)

            # Lancer la transcription async uniquement quand l'entrée est audio
            if recording_mode == 'audio_recording':
                start_transcription_async(reve.id)

            return JsonResponse({
                'success': True,
                'message': (
                    'Rêve enregistré ! La transcription arrivera dans quelques minutes...'
                    if recording_mode == 'audio_recording'
                    else 'Rêve enregistré !'
                ),
                'reve_id': reve.id,
            })

        except Exception as error:
            print(f'❌ Erreur enregistrement rêve: {error}')
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(error)}'
            }, status=500)


class ModifierReveView(LoginRequiredMixin, View):
    """
    Vue pour modifier un rêve existant (transcription et métadonnées)
    """

    def get(self, request, reve_id):
        """Afficher la page de modification avec les données du rêve"""
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.error(request, "Profil utilisateur introuvable")
            return HttpResponseRedirect(reverse("reves:index"))
        
        # Récupérer le rêve et vérifier qu'il appartient à l'utilisateur
        reve = get_object_or_404(Reve, id=reve_id, profil=profil)
        
        # Récupérer les émotions pour le formulaire
        emotions = ReveEmotion.objects.all().order_by('ordre')
        custom_emotions = ReveEmotionCustom.objects.filter(profil=profil).order_by('libelle')
        custom_elements = ReveElementCustom.objects.filter(profil=profil).order_by('libelle')
        images_modalites = ReveImageModalite.objects.all().order_by('ordre')
        predefined_elements = ['Travail', 'Famille', 'Amis']
        reve_elements = reve.elements_reve or []
        custom_elements_labels = [element.libelle for element in custom_elements]
        reve_elements_custom_selected = [
            element for element in reve_elements
            if element not in predefined_elements and element not in custom_elements_labels
        ]
        
        context = {
            "title": "Modifier le rêve",
            "reve": reve,
            "emotions": emotions,
            "custom_emotions": custom_emotions,
            "custom_elements": custom_elements,
            "images_modalites": images_modalites,
            "reve_emotions_ids": list(reve.emotions_reve.values_list('id', flat=True)),
            "reve_emotions_custom": list(reve.emotions_custom.values_list('libelle', flat=True)),
            "reve_modalites_ids": list(reve.images_modalites.values_list('id', flat=True)),
            "reve_elements": reve_elements,
            "reve_elements_custom_selected": reve_elements_custom_selected,
        }
        
        # Ajouter les infos questionnaire
        context = add_questionnaire_context(context, profil)
        
        return render(request, "reves/modifier_reve.html", context)

    def post(self, request, reve_id):
        """Gérer la mise à jour du rêve"""
        try:
            # Vérifier que l'utilisateur a un profil
            try:
                profil = request.user.profil
            except Profil.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil utilisateur introuvable'
                }, status=400)

            # Récupérer le rêve et vérifier qu'il appartient à l'utilisateur
            reve = get_object_or_404(Reve, id=reve_id, profil=profil)

            # Récupérer les données du formulaire
            transcription = request.POST.get('transcription', '').strip()
            type_reve = request.POST.get('type_reve', '').strip()
            etendue_reve = request.POST.get('etendue_reve', '')
            sens = request.POST.get('sens', '')
            emotions_ids = request.POST.getlist('emotions_reve')
            emotions_custom = request.POST.getlist('emotions_custom')
            elements_predefined = request.POST.getlist('elements_reve')
            elements_custom = request.POST.getlist('elements_custom')
            temps_selected = set(request.POST.getlist('temps_reve'))
            commentaire_libre = request.POST.get('commentaire_libre', '').strip()
            images_modalites_ids = request.POST.getlist('images_modalites')

            # Mettre à jour le rêve
            if transcription:
                reve.transcription = transcription
            reve.type_reve = type_reve if type_reve else None
            reve.etendue_reve = int(etendue_reve) if etendue_reve else None
            reve.sens = int(sens) if sens else None
            reve.temps_passe_lointain = 'passe_lointain' in temps_selected
            reve.temps_passe_recent = 'passe_recent' in temps_selected
            reve.temps_veille = 'veille' in temps_selected
            reve.temps_futur_proche = 'futur_proche' in temps_selected
            reve.temps_futur_lointain = 'futur_lointain' in temps_selected
            reve.temps_difficile = 'difficile' in temps_selected
            reve.commentaire_libre = commentaire_libre if commentaire_libre else None
            reve.save()

            # Mettre à jour les émotions
            if emotions_ids:
                emotions = ReveEmotion.objects.filter(id__in=emotions_ids)
                reve.emotions_reve.set(emotions)
            else:
                reve.emotions_reve.clear()

            # Mettre à jour les émotions personnalisées
            if emotions_custom:
                custom_objects = []
                for raw_value in emotions_custom:
                    cleaned_value = (raw_value or '').strip()
                    if not cleaned_value:
                        continue
                    existing = ReveEmotionCustom.objects.filter(
                        profil=profil,
                        libelle__iexact=cleaned_value
                    ).first()
                    if existing:
                        custom_objects.append(existing)
                        continue
                    custom_objects.append(ReveEmotionCustom.objects.create(
                        profil=profil,
                        libelle=cleaned_value
                    ))
                if custom_objects:
                    reve.emotions_custom.set(custom_objects)
            else:
                reve.emotions_custom.clear()

            # Mettre à jour les éléments liés au rêve
            selected_elements = []
            for value in elements_predefined:
                cleaned = (value or '').strip()
                if cleaned and cleaned not in selected_elements:
                    selected_elements.append(cleaned)

            if elements_custom:
                for raw_value in elements_custom:
                    cleaned_value = (raw_value or '').strip()
                    if not cleaned_value:
                        continue
                    existing = ReveElementCustom.objects.filter(
                        profil=profil,
                        libelle__iexact=cleaned_value
                    ).first()
                    if not existing:
                        existing = ReveElementCustom.objects.create(
                            profil=profil,
                            libelle=cleaned_value
                        )
                    if existing.libelle not in selected_elements:
                        selected_elements.append(existing.libelle)

            reve.elements_reve = selected_elements
            reve.save(update_fields=['elements_reve'])

            # Mettre à jour les modalités d'images
            if images_modalites_ids:
                images_modalites = ReveImageModalite.objects.filter(id__in=images_modalites_ids)
                reve.images_modalites.set(images_modalites)
            else:
                reve.images_modalites.clear()

            return JsonResponse({
                'success': True,
                'message': 'Rêve modifié avec succès !',
                'reve_id': reve.id,
            })

        except Exception as error:
            print(f'❌ Erreur modification rêve: {error}')
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(error)}'
            }, status=500)


class JournalView(LoginRequiredMixin, View):

    def get(self, request):
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.warning(request, "Veuillez completer votre profil d'abord.")
            return HttpResponseRedirect(reverse("reves:profil"))

        journal_data = get_journal_data(profil)

        context = {
            "profil": profil,
            "total_reves": journal_data['total_reves'],
            "reves": journal_data['reves'],
            "stats_mensuelles": journal_data['stats_mensuelles'],
            # Convertir les données pour Chart.js en JSON valide
            "emotions_labels": json.dumps(journal_data['emotions_labels'], ensure_ascii=False),
            "emotions_counts": json.dumps(journal_data['emotions_counts']),
            "etendue_labels": json.dumps(journal_data['etendue_labels'], ensure_ascii=False),
            "etendue_counts": json.dumps(journal_data['etendue_counts']),
        }
        
        # Ajouter les infos questionnaire
        context = add_questionnaire_context(context, profil)

        return render(request, "reves/journal.html", context)


class ReveDetailView(LoginRequiredMixin, generic.DetailView):
    model = Reve
    template_name = "reves/detail.html"
    context_object_name = "reve"

    def get_queryset(self):
        return Reve.objects.filter(profil=self.request.user.profil)


class ReveAudioDownloadView(View):
    """
    Vue sécurisée pour lire les fichiers audio
    Vérifie que l'utilisateur est propriétaire du rêve
    """

    AUDIO_MIME_BY_EXTENSION = {
        '.wav': 'audio/wav',
        '.m4a': 'audio/mp4',
        '.mp4a': 'audio/mp4',
        '.mp4': 'audio/mp4',
        '.webm': 'audio/webm',
    }

    def _get_audio_content_type(self, audio_name):
        extension = os.path.splitext(audio_name or '')[1].lower()
        if extension in self.AUDIO_MIME_BY_EXTENSION:
            return self.AUDIO_MIME_BY_EXTENSION[extension]

        guessed_type, _ = mimetypes.guess_type(audio_name or '')
        return guessed_type or 'application/octet-stream'

    def get(self, request, reve_id):
        """Retourne le fichier audio d'un rêve en lecture inline."""
        if not request.user.is_authenticated:
            return HttpResponse(status=403)

        reve = get_object_or_404(
            Reve.objects.select_related('user', 'profil__user'),
            id=reve_id,
        )

        is_owner = (
            reve.user_id == request.user.id
            or (reve.user_id is None and reve.profil.user_id == request.user.id)
        )
        if not (is_owner or request.user.is_superuser):
            return HttpResponse(status=403)

        if not reve.audio:
            return HttpResponse(status=404)

        try:
            audio_name = os.path.basename(reve.audio.name or f'reve-{reve.id}.wav')
            response = FileResponse(
                reve.audio.open('rb'),
                as_attachment=False,
                filename=audio_name,
                content_type=self._get_audio_content_type(audio_name),
            )
            response['Content-Disposition'] = f'inline; filename="{audio_name}"'
            return response
        except Exception as error:
            messages.error(request, f"Erreur lors du téléchargement: {error}")
            return HttpResponseRedirect(reverse("reves:journal"))


class ExportRevesCsvView(LoginRequiredMixin, View):
    """Exporte les rêves de l'utilisateur connecté en CSV."""

    def get(self, request):
        allowed, retry_after = _rate_limit(
            request.user.id,
            scope='export_csv',
            limit=EXPORT_RATE_LIMIT,
            window_seconds=EXPORT_RATE_WINDOW_SECONDS,
        )
        if not allowed:
            messages.error(
                request,
                f"Trop d'exports CSV. Réessayez dans {retry_after} secondes.",
            )
            return HttpResponseRedirect(reverse("reves:profil"))

        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.error(request, "Profil utilisateur introuvable")
            return HttpResponseRedirect(reverse("reves:profil"))

        reves = Reve.objects.filter(profil=profil).prefetch_related(
            'emotions_reve',
            'emotions_custom',
            'images_modalites',
        ).order_by('-date', '-created_at')

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reves_{request.user.username}.csv"'
        response.write('\ufeff')  # BOM for Excel UTF-8 support

        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'id',
            'date',
            'created_at',
            'existence_souvenir',
            'type_reve',
            'etendue_reve',
            'sens',
            'temps_passe_lointain',
            'temps_passe_recent',
            'temps_veille',
            'temps_futur_proche',
            'temps_futur_lointain',
            'temps_difficile',
            'elements_reve',
            'emotions_reve',
            'emotions_custom',
            'images_modalites',
            'commentaire_libre',
            'transcription',
            'transcription_ready',
            'audio_url',
        ])

        for reve in reves:
            emotions = ', '.join(reve.emotions_reve.values_list('libelle', flat=True))
            emotions_custom = ', '.join(reve.emotions_custom.values_list('libelle', flat=True))
            modalites = ', '.join(reve.images_modalites.values_list('libelle', flat=True))
            elements = ', '.join(reve.elements_reve or [])

            row = [
                reve.id,
                reve.date.isoformat() if reve.date else '',
                reve.created_at.isoformat() if reve.created_at else '',
                'oui' if reve.existence_souvenir else 'non',
                reve.get_type_reve_display() if reve.type_reve else '',
                reve.get_etendue_reve_display() if reve.etendue_reve else '',
                reve.get_sens_display() if reve.sens else '',
                'oui' if reve.temps_passe_lointain else 'non',
                'oui' if reve.temps_passe_recent else 'non',
                'oui' if reve.temps_veille else 'non',
                'oui' if reve.temps_futur_proche else 'non',
                'oui' if reve.temps_futur_lointain else 'non',
                'oui' if reve.temps_difficile else 'non',
                elements,
                emotions,
                emotions_custom,
                modalites,
                reve.commentaire_libre or '',
                reve.transcription or '',
                'oui' if reve.transcription_ready else 'non',
                reve.audio.url if reve.audio else '',
            ]
            writer.writerow([_safe_csv_cell(value) for value in row])

        return response


class ReveTranscriptionUpdateView(LoginRequiredMixin, View):
    """Mettre a jour la transcription d'un reve depuis le journal."""

    def post(self, request, reve_id):
        try:
            reve = Reve.objects.get(id=reve_id, profil=request.user.profil)
        except Reve.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Reve non trouve'
            }, status=404)

        transcription = None
        if request.content_type and 'application/json' in request.content_type:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Donnees invalides'
                }, status=400)
            transcription = data.get('transcription', '')
        else:
            transcription = request.POST.get('transcription', '')

        if transcription is None:
            return JsonResponse({
                'success': False,
                'message': 'Transcription manquante'
            }, status=400)

        transcription = transcription.strip()
        reve.transcription = transcription
        reve.transcription_ready = bool(transcription)
        reve.save(update_fields=['transcription', 'transcription_ready'])

        return JsonResponse({
            'success': True,
            'message': 'Transcription mise a jour'
        })


class QuestionnaireView(View):
    """
    Vue pour gérer le questionnaire sur les rêves
    Affiche le formulaire et traite la soumission
    Restriction : accessible uniquement 1 semaine après la création du profil
    """
    template_name = "reves/questionnaire.html"
    waiting_template_name = "reves/questionnaire_waiting.html"
    
    def get(self, request):
        """Afficher le formulaire de questionnaire ou la page d'attente"""
        # Vérifier si l'utilisateur est connecté
        if not request.user.is_authenticated:
            messages.warning(request, "Vous devez être connecté pour accéder au questionnaire.")
            return HttpResponseRedirect(reverse("login"))
        
        # Vérifier si l'utilisateur peut accéder au questionnaire
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.error(request, "Profil utilisateur introuvable. Veuillez contacter l'administrateur.")
            return HttpResponseRedirect(reverse("reves:index"))

        completed_count = Questionnaire.objects.filter(
            profil=profil,
            is_completed=True,
        ).count()
        if completed_count >= MAX_QUESTIONNAIRE_SUBMISSIONS:
            messages.info(
                request,
                "Vous avez déjà atteint la limite de 5 soumissions complètes du questionnaire.",
            )
            return HttpResponseRedirect(reverse("reves:profil"))
        
        if not profil.can_access_questionnaire():
            # Afficher la page d'attente
            from django.utils import timezone
            access_date = profil.questionnaire_access_reference_date() + timezone.timedelta(days=7)
            context = {
                'days_remaining': profil.days_until_questionnaire_access(),
                'access_date': access_date,
                'is_authenticated': True
            }
            return render(request, self.waiting_template_name, context)
        
        # L'utilisateur peut accéder au questionnaire
        form = QuestionnaireForm()
        context = {
            'form': form,
            'is_authenticated': True
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Traiter la soumission du questionnaire"""
        import json
        from django.http import JsonResponse
        
        # Vérifier si l'utilisateur est connecté
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Vous devez être connecté.'}, status=401)
            messages.error(request, "Vous devez être connecté pour soumettre le questionnaire.")
            return HttpResponseRedirect(reverse("login"))
        
        # Vérifier si l'utilisateur peut accéder au questionnaire
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            error_msg = "Profil utilisateur introuvable."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return HttpResponseRedirect(reverse("reves:index"))

        completed_count = Questionnaire.objects.filter(
            profil=profil,
            is_completed=True,
        ).count()
        if completed_count >= MAX_QUESTIONNAIRE_SUBMISSIONS:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {
                        'success': False,
                        'message': 'Limite atteinte: maximum 5 soumissions complètes du questionnaire.',
                    },
                    status=403,
                )
            messages.error(request, "Limite atteinte: maximum 5 soumissions complètes du questionnaire.")
            return HttpResponseRedirect(reverse("reves:profil"))

        if not profil.can_access_questionnaire():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Accès non autorisé.'}, status=403)
            messages.error(request, "Vous devez attendre 1 semaine après la création de votre compte pour remplir le questionnaire.")
            return HttpResponseRedirect(reverse("reves:questionnaire"))
        
        # Check if this is an AJAX request (intermediate save during section navigation)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        section = request.POST.get('section')
        
        if is_ajax and section:
            # AJAX request - save section data to session for later
            if 'questionnaire_data' not in request.session:
                request.session['questionnaire_data'] = {}

            # Store the POST data for this section
            section_data = request.POST.dict()
            section_data.pop('csrfmiddlewaretoken', None)  # Remove CSRF token

            request.session['questionnaire_data'][f'section_{section}'] = section_data
            request.session.modified = True

            # Calculate and store section timing if provided
            section_duration = request.POST.get('section_duration')
            if section_duration:
                try:
                    parsed_duration = float(section_duration)
                    if (
                        QUESTIONNAIRE_MIN_SECTION_DURATION_SECONDS
                        <= parsed_duration
                        <= QUESTIONNAIRE_MAX_SECTION_DURATION_SECONDS
                    ):
                        if 'section_timings' not in request.session:
                            request.session['section_timings'] = {}
                        request.session['section_timings'][f'section_{section}'] = parsed_duration
                        request.session.modified = True
                except (TypeError, ValueError):
                    # Ignore invalid duration to avoid client-side metric poisoning.
                    pass

            # --- Sauvegarde partielle en base de données ---
            # Champs par section (checkboxes booléennes vs radios True/False vs autres)
            BOOL_CHECKBOX_FIELDS = {
                'mod_img', 'mod_son', 'mod_sens', 'mod_emot', 'mod_pens',
                'img_coul', 'img_nb', 'img_net', 'img_flou', 'img_ns',
                'aide_medic', 'aide_tisane', 'aide_autre',
                'pens_trav', 'pens_fin', 'pens_fam', 'pens_proch', 'pens_actu',
                'pens_autre', 'pens_rien',
                'cont_tv', 'cont_series_films', 'cont_rs', 'cont_jeux',
                'cont_livres', 'cont_rien', 'cont_autre',
                'composition_logement_seul', 'composition_logement_conjoint',
                'composition_logement_enfants', 'composition_logement_ami_parent_heberge',
                'composition_logement_colocataire', 'composition_logement_parent_grand_parent',
                'composition_logement_autres',
                'discri_age', 'discri_genre', 'discri_sante_physique', 'discri_sante_mentale',
                'discri_couleur_peau', 'discri_origine_nationalite', 'discri_situation_familiale',
                'discri_orientation_sexuelle', 'discri_autre',
                'discri_contexte_emploi', 'discri_contexte_logement', 'discri_contexte_travail',
                'discri_contexte_education', 'discri_contexte_sante', 'discri_contexte_famille',
                'discri_contexte_autre',
            }
            BOOL_RADIO_FIELDS = {
                'a_deja_travaille', 'fonction_management', 'reveil_nuit', 'aide_sommeil',
            }
            INT_FIELDS = {
                'annee_naissance', 'niv_diplome', 'revenus_tranche', 'travail_statut',
                'genre', 'habitat', 'profession',
                'freq_reves_not', 'etendue_souvenir_reve', 'temps_du_reve',
                'latence_som', 'nuits_reveil', 'duree_eveil',
                'statut_couple', 'nb_enfants_cohabitants', 'nb_enfants_moins14',
                'pere_niv_diplome', 'pere_csp', 'mere_niv_diplome', 'mere_csp',
                'conj_niv_diplome', 'conj_csp', 'lieu_naissance', 'lieu_naissance_pere',
                'perception_financiere', 'perception_risque_pauvrete', 'position_subjective_classe',
                'perception_mobilite', 'discri_presence', 'sante_generale',
                'det_1', 'det_2', 'det_3', 'det_4', 'det_5',
            }
            TIME_FIELDS = {'heure_coucher', 'heure_reveil', 'besoin_som'}

            SECTION_FIELDS = {
                '1': [
                    'freq_reves_not', 'mod_img', 'mod_son', 'mod_sens', 'mod_emot', 'mod_pens',
                    'img_coul', 'img_nb', 'img_net', 'img_flou', 'img_ns',
                    'etendue_souvenir_reve', 'temps_du_reve',
                    'heure_coucher', 'heure_reveil', 'latence_som', 'besoin_som',
                    'reveil_nuit', 'nuits_reveil', 'duree_eveil',
                    'aide_sommeil', 'aide_medic', 'aide_tisane', 'aide_autre',
                    'pens_trav', 'pens_fin', 'pens_fam', 'pens_proch', 'pens_actu',
                    'pens_autre', 'pens_rien', 'pens_autre_txt',
                    'cont_tv', 'cont_series_films', 'cont_rs', 'cont_jeux',
                    'cont_livres', 'cont_rien', 'cont_autre',
                ],
                '2': [
                    'perception_financiere', 'perception_risque_pauvrete',
                    'position_subjective_classe', 'perception_mobilite',
                    'discri_presence',
                    'discri_age', 'discri_genre', 'discri_sante_physique', 'discri_sante_mentale',
                    'discri_couleur_peau', 'discri_origine_nationalite', 'discri_situation_familiale',
                    'discri_orientation_sexuelle', 'discri_autre', 'discri_autre_precision',
                    'discri_contexte_emploi', 'discri_contexte_logement', 'discri_contexte_travail',
                    'discri_contexte_education', 'discri_contexte_sante', 'discri_contexte_famille',
                    'discri_contexte_autre',
                    'sante_generale', 'det_1', 'det_2', 'det_3', 'det_4', 'det_5',
                ],
                '3': [
                    'annee_naissance', 'genre', 'habitat', 'niv_diplome', 'revenus_tranche',
                    'travail_statut', 'a_deja_travaille', 'profession', 'fonction_management',
                    'statut_couple',
                    'composition_logement_seul', 'composition_logement_conjoint',
                    'composition_logement_enfants', 'composition_logement_ami_parent_heberge',
                    'composition_logement_colocataire', 'composition_logement_parent_grand_parent',
                    'composition_logement_autres',
                    'nb_enfants_cohabitants', 'nb_enfants_moins14',
                    'pere_niv_diplome', 'pere_csp',
                    'mere_niv_diplome', 'mere_csp',
                    'conj_niv_diplome', 'conj_csp',
                    'lieu_naissance', 'lieu_naissance_pere',
                ],
            }

            questionnaire_id = request.session.get('questionnaire_id')
            q = None
            if questionnaire_id:
                try:
                    q = Questionnaire.objects.get(id=questionnaire_id, profil=profil)
                except Questionnaire.DoesNotExist:
                    q = None
            if q is None:
                q = Questionnaire(profil=profil, user=request.user)

            for field_name in SECTION_FIELDS.get(str(section), []):
                if field_name in BOOL_CHECKBOX_FIELDS:
                    setattr(q, field_name, field_name in request.POST)
                elif field_name in BOOL_RADIO_FIELDS:
                    val = request.POST.get(field_name)
                    if val is not None:
                        setattr(q, field_name, val == 'True')
                elif field_name in INT_FIELDS:
                    val = request.POST.get(field_name)
                    if val:
                        try:
                            setattr(q, field_name, int(val))
                        except (ValueError, TypeError):
                            pass
                elif field_name in TIME_FIELDS:
                    val = request.POST.get(field_name)
                    if val:
                        setattr(q, field_name, val)
                else:
                    val = request.POST.get(field_name)
                    if val is not None:
                        setattr(q, field_name, val)

            q.save()
            request.session['questionnaire_id'] = q.id
            request.session.modified = True
            # --- Fin sauvegarde partielle ---

            return JsonResponse({'success': True, 'message': 'Section enregistrée.'})
        
        # Regular form submission (final submit)
        questionnaire_id = request.session.get('questionnaire_id')
        instance = None
        if questionnaire_id:
            try:
                instance = Questionnaire.objects.get(id=questionnaire_id, profil=profil)
            except Questionnaire.DoesNotExist:
                instance = None

        form = QuestionnaireForm(request.POST, instance=instance)
        
        if form.is_valid():
            with transaction.atomic():
                profil_locked = Profil.objects.select_for_update().get(pk=profil.pk)
                completed_count = Questionnaire.objects.filter(
                    profil=profil_locked,
                    is_completed=True,
                ).count()

                if completed_count >= MAX_QUESTIONNAIRE_SUBMISSIONS:
                    if is_ajax:
                        return JsonResponse(
                            {
                                'success': False,
                                'message': 'Limite atteinte: maximum 5 soumissions complètes du questionnaire.',
                            },
                            status=403,
                        )
                    messages.error(request, "Limite atteinte: maximum 5 soumissions complètes du questionnaire.")
                    return HttpResponseRedirect(reverse("reves:profil"))

                now_ts = int(time.time())
                last_submit_at = int(request.session.get('questionnaire_last_submit_at', 0) or 0)
                last_submit_id = request.session.get('questionnaire_last_submission_id')
                duplicate_window_active = (
                    not questionnaire_id
                    and last_submit_id
                    and (now_ts - last_submit_at) <= QUESTIONNAIRE_DUPLICATE_SUBMIT_WINDOW_SECONDS
                )
                if duplicate_window_active:
                    messages.info(request, "Soumission déjà enregistrée.")
                    return HttpResponseRedirect(reverse("reves:profil"))

                questionnaire = form.save(commit=False)
                questionnaire.profil = profil_locked
                questionnaire.user = request.user
                questionnaire.is_completed = True
                questionnaire.completed_at = timezone.now()
                questionnaire.submission_number = completed_count + 1

                section_timings = request.session.get('section_timings', {})
                total_duration = None
                if section_timings:
                    safe_values = []
                    for value in section_timings.values():
                        try:
                            parsed = float(value)
                            if (
                                QUESTIONNAIRE_MIN_SECTION_DURATION_SECONDS
                                <= parsed
                                <= QUESTIONNAIRE_MAX_SECTION_DURATION_SECONDS
                            ):
                                safe_values.append(parsed)
                        except (TypeError, ValueError):
                            continue
                    if safe_values:
                        total_duration = int(sum(safe_values))
                elif questionnaire.created_at:
                    total_duration = max(
                        0,
                        int((questionnaire.completed_at - questionnaire.created_at).total_seconds()),
                    )

                questionnaire.completion_duration_seconds = total_duration
                questionnaire.save()
            
            # Clear session data
            request.session.pop('questionnaire_data', None)
            request.session.pop('section_timings', None)
            request.session.pop('questionnaire_id', None)
            request.session['questionnaire_last_submit_at'] = int(time.time())
            request.session['questionnaire_last_submission_id'] = questionnaire.id
            request.session.modified = True
            
            messages.success(request, "Merci d'avoir complété le questionnaire ! Vos réponses ont été enregistrées.")
            return HttpResponseRedirect(reverse("reves:profil"))
        else:
            if is_ajax:
                # Return errors as JSON
                errors = {field: str(error[0]) for field, error in form.errors.items()}
                return JsonResponse({'success': False, 'message': 'Erreur de validation.', 'errors': errors}, status=400)
            
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
            context = {
                'form': form,
                'is_authenticated': request.user.is_authenticated
            }
            return render(request, self.template_name, context)


class WelcomeView(LoginRequiredMixin, View):
    """
    Vue d'accueil après création de compte
    Affiche une page de bienvenue avec un modal élégant
    """
    template_name = "reves/welcome.html"
    
    def get(self, request):
        """Afficher la page de bienvenue"""
        return render(request, self.template_name)


class SignUpView(View):
    """
    Vue pour l'inscription avec consentement.
    Sécurité:
    - Utilise UserCreationForm pour le hashage sécurisé des mots de passe (PBKDF2)
    - Validation des mots de passe selon les standards Django
    - CSRF protection via CsrfViewMiddleware (déjà activé)
    - Validation de l'email unique
    - Transaction atomique pour éviter les users orphelins
    """
    template_name = 'registration/signup.html'
    form_class = SignUpForm
    
    def get(self, request):
        """Afficher le formulaire d'inscription"""
        if request.user.is_authenticated:
            return redirect('reves:index')
        
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """Traiter l'inscription"""
        if request.user.is_authenticated:
            return redirect('reves:index')
        
        form = self.form_class(request.POST)
        
        if form.is_valid():
            try:
                from django.db import IntegrityError
                
                # Sauvegarder l'utilisateur et le profil avec les consentements
                # (utilise transaction.atomic donc tout est rollbacké en cas d'erreur)
                user = form.save()
                
                # Authentifier et connecter l'utilisateur automatiquement
                user = authenticate(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1']
                )
                
                if user is not None:
                    login(request, user)
                    messages.success(
                        request,
                        f'Bienvenue {user.username} ! Votre compte a été créé avec succès.'
                    )
                    return redirect('reves:welcome')
                else:
                    # Ne devrait pas arriver ici normalement, mais en cas d'erreur,
                    # proposer à l'utilisateur de se connecter
                    messages.warning(
                        request,
                        'Votre compte a été créé ! Veuillez vous connecter pour continuer.'
                    )
                    return redirect('login')
            
            except IntegrityError as e:
                # Erreur d'intégrité : doublon d'email généralement
                if 'email' in str(e).lower() or 'unique' in str(e).lower():
                    messages.error(
                        request,
                        'Cet email est déjà utilisé. Veuillez en choisir un autre ou vous connecter si vous avez déjà un compte.'
                    )
                else:
                    messages.error(
                        request,
                        f'Erreur lors de la création du compte: {str(e)}'
                    )
                return render(request, self.template_name, {'form': form})
            
            except Exception as e:
                # Autres erreurs
                messages.error(
                    request,
                    f'Une erreur inattendue est survenue: {str(e)}'
                )
                return render(request, self.template_name, {'form': form})
        else:
            # Le formulaire contient des erreurs de validation
            # On affiche le formulaire avec les messages d'erreur
            return render(request, self.template_name, {'form': form})


class AccueilView(View):
    """
    Page d'accueil publique
    Visible pour tous les utilisateurs (connectés ou non)
    """
    template_name = "reves/index.html"
    
    def get(self, request):
        """Afficher la page d'accueil"""
        context = {
            'is_authenticated': request.user.is_authenticated,
        }
        return render(request, self.template_name, context)


# VUES POUR LES NOTIFICATIONS ========================

class NotificationsListView(LoginRequiredMixin, View):
    """Récupérer toutes les notifications de l'utilisateur (API)"""
    
    def get(self, request):
        """Retourner les notifications au format JSON"""
        allowed, retry_after = _rate_limit(
            request.user.id,
            scope='notifications_read',
            limit=NOTIFICATIONS_READ_RATE_LIMIT,
            window_seconds=NOTIFICATIONS_READ_RATE_WINDOW_SECONDS,
        )
        if not allowed:
            return _rate_limited_json_response(
                retry_after,
                "Trop de requêtes notifications. Réessayez plus tard.",
            )

        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=400)
        
        # Récupérer les notifications (non lues en priorité)
        notifications = Notification.objects.filter(
            profil=profil
        ).order_by('-created_at')[:50]  # Limiter à 50 dernières
        
        data = {
            'success': True,
            'notifications': [
                {
                    'id': notif.id,
                    'type': notif.notification_type,
                    'title': notif.title,
                    'message': notif.message,
                    'is_read': notif.is_read,
                    'created_at': notif.created_at.isoformat(),
                    'read_at': notif.read_at.isoformat() if notif.read_at else None,
                }
                for notif in notifications
            ],
            'unread_count': Notification.objects.filter(
                profil=profil,
                is_read=False
            ).count()
        }
        
        return JsonResponse(data)


class NotificationMarkAsReadView(LoginRequiredMixin, View):
    """Marquer une notification comme lue"""

    http_method_names = ['post']

    def post(self, request, notification_id):
        """Marquer une notification comme lue"""
        allowed, retry_after = _rate_limit(
            request.user.id,
            scope='notifications_mutation',
            limit=NOTIFICATIONS_MUTATION_RATE_LIMIT,
            window_seconds=NOTIFICATIONS_MUTATION_RATE_WINDOW_SECONDS,
        )
        if not allowed:
            return _rate_limited_json_response(
                retry_after,
                "Trop d'actions sur les notifications. Réessayez plus tard.",
            )

        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=400)
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                profil=profil
            )
            notification.mark_as_read()
            
            return JsonResponse({
                'success': True,
                'message': 'Notification marquée comme lue'
            })
        except Notification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Notification non trouvée'
            }, status=404)


class NotificationUnreadCountView(LoginRequiredMixin, View):
    """Obtenir le nombre de notifications non lues"""
    
    def get(self, request):
        """Retourner le nombre de notifications non lues"""
        allowed, retry_after = _rate_limit(
            request.user.id,
            scope='notifications_read',
            limit=NOTIFICATIONS_READ_RATE_LIMIT,
            window_seconds=NOTIFICATIONS_READ_RATE_WINDOW_SECONDS,
        )
        if not allowed:
            return _rate_limited_json_response(
                retry_after,
                "Trop de requêtes notifications. Réessayez plus tard.",
            )

        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=400)
        
        unread_count = Notification.objects.filter(
            profil=profil,
            is_read=False
        ).count()
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count
        })


class NotificationDeleteView(LoginRequiredMixin, View):
    """Supprimer une notification"""

    http_method_names = ['delete']

    def delete(self, request, notification_id):
        """Supprimer une notification"""
        allowed, retry_after = _rate_limit(
            request.user.id,
            scope='notifications_mutation',
            limit=NOTIFICATIONS_MUTATION_RATE_LIMIT,
            window_seconds=NOTIFICATIONS_MUTATION_RATE_WINDOW_SECONDS,
        )
        if not allowed:
            return _rate_limited_json_response(
                retry_after,
                "Trop d'actions sur les notifications. Réessayez plus tard.",
            )

        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil non trouvé'
            }, status=400)
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                profil=profil
            )
            notification.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Notification supprimée'
            })
        except Notification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Notification non trouvée'
            }, status=404)