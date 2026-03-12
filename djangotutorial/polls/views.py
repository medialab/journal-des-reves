from django.db.models import F
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, JsonResponse, FileResponse, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.views import generic, View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
import uuid
import os
import json
import csv

from .models import Reve, Profil, Questionnaire, ReveEmotion, ReveEmotionCustom, ReveElementCustom, ReveImageModalite, Notification
from .services.journal_service import get_journal_data
from .services.transcription_service import start_transcription_async
from .forms import ReveForm, QuestionnaireForm, SignUpForm


# Helper functions
def add_questionnaire_context(context, profil):
    """Ajouter les informations de questionnaire au contexte"""
    has_questionnaire = Questionnaire.objects.filter(profil=profil).exists()
    context['has_questionnaire'] = has_questionnaire
    return context


class ProfilView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.error(request, "Profil non trouve. Veuillez contacter l'administrateur.")
            return HttpResponseRedirect(reverse("polls:index"))

        journal_data = get_journal_data(profil)

        context = {
            "profil": profil,
            "user": request.user,
            **journal_data
        }
        
        # Ajouter les infos questionnaire
        context = add_questionnaire_context(context, profil)

        return render(request, "polls/profil.html", context)
    
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
    template_name = "polls/description.html"
    
    def get(self, request):
        return render(request, self.template_name)



class EnregistrerView(LoginRequiredMixin, View):
    """
    Vue pour enregistrer un nouveau rêve avec audio et métadonnées
    La transcription est traitée de manière asynchrone avec Whisper
    """

    def get(self, request):
        """Afficher la page d'enregistrement"""
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.error(request, "Profil utilisateur introuvable")
            return HttpResponseRedirect(reverse("polls:index"))
        
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
        }
        
        # Ajouter les infos questionnaire
        context = add_questionnaire_context(context, profil)
        
        return render(request, "polls/enregistrer.html", context)

    def post(self, request):
        """Gérer l'upload de l'audio et la sauvegarde du rêve"""
        try:
            # Vérifier que l'utilisateur a un profil
            try:
                profil = request.user.profil
            except Profil.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil utilisateur introuvable'
                }, status=400)

            # Récupérer existence_souvenir (par défaut True)
            existence_souvenir_str = request.POST.get('existence_souvenir', '1')
            existence_souvenir = existence_souvenir_str == '1'

            # Si la personne n'a aucun souvenir, créer un rêve vide
            if not existence_souvenir:
                reve = Reve.objects.create(
                    profil=profil,
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
            type_reve = request.POST.get('type_reve', '').strip()
            etendue_reve = request.POST.get('etendue_reve', '')
            sens = request.POST.get('sens', '')
            emotions_ids = request.POST.getlist('emotions_reve')
            emotions_custom = request.POST.getlist('emotions_custom')
            elements_predefined = request.POST.getlist('elements_reve')
            elements_custom = request.POST.getlist('elements_custom')
            temps_reve = request.POST.get('temps_reve', '').strip()
            commentaire_libre = request.POST.get('commentaire_libre', '').strip()
            images_modalites_ids = request.POST.getlist('images_modalites')

            # Validation
            if not audio_file:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun fichier audio fourni'
                }, status=400)

            # Créer le rêve avec le fichier audio
            reve = Reve.objects.create(
                profil=profil,
                audio=audio_file,
                type_reve=type_reve if type_reve else None,
                etendue_reve=int(etendue_reve) if etendue_reve else None,
                sens=int(sens) if sens else None,
                temps_reve=temps_reve if temps_reve else None,
                commentaire_libre=commentaire_libre if commentaire_libre else None,
                existence_souvenir=True,
                transcription_ready=False
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

            # Lancer la transcription en arrière-plan de manière asynchrone et non-bloquante
            start_transcription_async(reve.id)

            return JsonResponse({
                'success': True,
                'message': 'Rêve enregistré ! La transcription arrivera dans quelques minutes...',
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
            return HttpResponseRedirect(reverse("polls:index"))
        
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
        
        return render(request, "polls/modifier_reve.html", context)

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
            temps_reve = request.POST.get('temps_reve', '').strip()
            commentaire_libre = request.POST.get('commentaire_libre', '').strip()
            images_modalites_ids = request.POST.getlist('images_modalites')

            # Mettre à jour le rêve
            if transcription:
                reve.transcription = transcription
            reve.type_reve = type_reve if type_reve else None
            reve.etendue_reve = int(etendue_reve) if etendue_reve else None
            reve.sens = int(sens) if sens else None
            reve.temps_reve = temps_reve if temps_reve else None
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
            return HttpResponseRedirect(reverse("polls:profil"))

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

        return render(request, "polls/journal.html", context)


class ReveDetailView(LoginRequiredMixin, generic.DetailView):
    model = Reve
    template_name = "polls/reve_detail.html"
    context_object_name = "reve"

    def get_queryset(self):
        return Reve.objects.filter(profil=self.request.user.profil)


class ReveAudioDownloadView(LoginRequiredMixin, View):
    """
    Vue sécurisée pour télécharger les fichiers audio
    Vérifie que l'utilisateur est propriétaire du rêve
    """

    def get(self, request, reve_id):
        """Télécharger le fichier audio d'un rêve"""
        try:
            reve = Reve.objects.get(id=reve_id, profil=request.user.profil)
        except Reve.DoesNotExist:
            messages.error(request, "Rêve non trouvé ou accès refusé")
            return HttpResponseRedirect(reverse("polls:journal"))

        if not reve.audio:
            messages.error(request, "Aucun fichier audio pour ce rêve")
            return HttpResponseRedirect(reverse("polls:journal"))

        try:
            # Ouvrir le fichier audio
            response = FileResponse(
                reve.audio.open('rb'),
                as_attachment=True,
                filename=f'reve-{reve.id}.wav'
            )
            response['Content-Type'] = 'audio/wav'
            return response
        except Exception as error:
            messages.error(request, f"Erreur lors du téléchargement: {error}")
            return HttpResponseRedirect(reverse("polls:journal"))


class ExportRevesCsvView(LoginRequiredMixin, View):
    """Exporte les rêves de l'utilisateur connecté en CSV."""

    def get(self, request):
        try:
            profil = request.user.profil
        except Profil.DoesNotExist:
            messages.error(request, "Profil utilisateur introuvable")
            return HttpResponseRedirect(reverse("polls:profil"))

        reves = Reve.objects.filter(profil=profil).prefetch_related(
            'emotions_reve',
            'emotions_custom',
            'images_modalites',
            'tags',
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
            'temps_reve',
            'elements_reve',
            'emotions_reve',
            'emotions_custom',
            'images_modalites',
            'tags',
            'commentaire_libre',
            'transcription',
            'transcription_ready',
            'audio_url',
        ])

        for reve in reves:
            emotions = ', '.join(reve.emotions_reve.values_list('libelle', flat=True))
            emotions_custom = ', '.join(reve.emotions_custom.values_list('libelle', flat=True))
            modalites = ', '.join(reve.images_modalites.values_list('libelle', flat=True))
            tags = ', '.join(reve.tags.values_list('libelle', flat=True))
            elements = ', '.join(reve.elements_reve or [])

            writer.writerow([
                reve.id,
                reve.date.isoformat() if reve.date else '',
                reve.created_at.isoformat() if reve.created_at else '',
                'oui' if reve.existence_souvenir else 'non',
                reve.get_type_reve_display() if reve.type_reve else '',
                reve.get_etendue_reve_display() if reve.etendue_reve else '',
                reve.get_sens_display() if reve.sens else '',
                reve.get_temps_reve_display() if reve.temps_reve else '',
                elements,
                emotions,
                emotions_custom,
                modalites,
                tags,
                reve.commentaire_libre or '',
                reve.transcription or '',
                'oui' if reve.transcription_ready else 'non',
                reve.audio.url if reve.audio else '',
            ])

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
    template_name = "polls/questionnaire.html"
    waiting_template_name = "polls/questionnaire_waiting.html"
    
    def get(self, request):
        """Afficher le formulaire de questionnaire ou la page d'attente"""
        # Vérifier si l'utilisateur est connecté
        if not request.user.is_authenticated:
            messages.warning(request, "Vous devez être connecté pour accéder au questionnaire.")
            return HttpResponseRedirect(reverse("login"))
        
        # Vérifier si l'utilisateur peut accéder au questionnaire
        profil = request.user.profil
        
        if not profil.can_access_questionnaire():
            # Afficher la page d'attente
            from django.utils import timezone
            access_date = profil.created_at + timezone.timedelta(days=7)
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
        profil = request.user.profil
        if not profil.can_access_questionnaire():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Accès non autorisé.'}, status=403)
            messages.error(request, "Vous devez attendre 1 semaine après la création de votre compte pour remplir le questionnaire.")
            return HttpResponseRedirect(reverse("polls:questionnaire"))
        
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
                if 'section_timings' not in request.session:
                    request.session['section_timings'] = {}
                request.session['section_timings'][f'section_{section}'] = float(section_duration)
                request.session.modified = True
            
            return JsonResponse({'success': True, 'message': 'Section enregistrée.'})
        
        # Regular form submission (final submit)
        form = QuestionnaireForm(request.POST)
        
        if form.is_valid():
            questionnaire = form.save(commit=False)
            questionnaire.profil = request.user.profil
            questionnaire.user = request.user
            questionnaire.save()
            
            # Clear session data
            request.session.pop('questionnaire_data', None)
            request.session.pop('section_timings', None)
            
            messages.success(request, "Merci d'avoir complété le questionnaire ! Vos réponses ont été enregistrées.")
            return HttpResponseRedirect(reverse("polls:profil"))
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
    template_name = "polls/welcome.html"
    
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
    """
    template_name = 'registration/signup.html'
    form_class = SignUpForm
    
    def get(self, request):
        """Afficher le formulaire d'inscription"""
        if request.user.is_authenticated:
            return redirect('polls:index')
        
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """Traiter l'inscription"""
        if request.user.is_authenticated:
            return redirect('polls:index')
        
        form = self.form_class(request.POST)
        
        if form.is_valid():
            try:
                # Sauvegarder l'utilisateur et le profil avec les consentements
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
                    return redirect('polls:welcome')
                else:
                    messages.error(
                        request,
                        'Une erreur est survenue lors de la connexion. Veuillez vous connecter manuellement.'
                    )
                    return redirect('login')
            
            except Exception as e:
                messages.error(
                    request,
                    f'Une erreur est survenue lors de la création du compte: {str(e)}'
                )
                return render(request, self.template_name, {'form': form})
        else:
            # Le formulaire contient des erreurs
            return render(request, self.template_name, {'form': form})


class AccueilView(View):
    """
    Page d'accueil publique
    Visible pour tous les utilisateurs (connectés ou non)
    """
    template_name = "polls/index.html"
    
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
    
    @require_http_methods(["POST"])
    def post(self, request, notification_id):
        """Marquer une notification comme lue"""
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
    
    @require_http_methods(["DELETE"])
    def delete(self, request, notification_id):
        """Supprimer une notification"""
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