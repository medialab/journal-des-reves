from django.db.models import F
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, JsonResponse, FileResponse
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

from .models import Choice, Question, Reve, Profil, Questionnaire
from .services.journal_service import get_journal_data
from .services.transcription_service import start_transcription_async
from .forms import ReveForm, QuestionnaireForm, SignUpForm


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
        
        if 'birth_year' in data:
            try:
                birth_year = int(data['birth_year'])
                if 1900 <= birth_year <= 2025:
                    profil.birth_year = birth_year
            except (ValueError, TypeError):
                pass
        
        if 'genre' in data and data['genre']:
            profil.genre = data['genre']
        
        if 'biography' in data:
            profil.biography = data['biography']
        
        if 'deja_ecrit_reve' in data:
            profil.deja_ecrit_reve = data['deja_ecrit_reve']
        
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

class DescriptionView(generic.DetailView):
    template_name = "polls/description.html"


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

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
        from .models import Emotion, EmotionCustom
        emotions = Emotion.objects.all().order_by('ordre')
        custom_emotions = EmotionCustom.objects.filter(profil=profil).order_by('libelle')
        
        context = {
            "title": "Enregistrer un rêve",
            "emotions": emotions,
            "custom_emotions": custom_emotions,
        }
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

            # Récupérer les données du formulaire
            audio_file = request.FILES.get('audio')
            type_reve = request.POST.get('type_reve', '').strip()
            etendue_reve = request.POST.get('etendue_reve', '')
            sens = request.POST.get('sens', '')
            emotions_ids = request.POST.getlist('emotions_reve')
            emotions_custom = request.POST.getlist('emotions_custom')

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
                transcription_ready=False
            )

            # Ajouter les émotions
            if emotions_ids:
                from .models import Emotion
                emotions = Emotion.objects.filter(id__in=emotions_ids)
                reve.emotions_reve.set(emotions)

            # Ajouter les émotions personnalisées
            if emotions_custom:
                from .models import EmotionCustom
                custom_objects = []
                for raw_value in emotions_custom:
                    cleaned_value = (raw_value or '').strip()
                    if not cleaned_value:
                        continue
                    existing = EmotionCustom.objects.filter(
                        profil=profil,
                        libelle__iexact=cleaned_value
                    ).first()
                    if existing:
                        custom_objects.append(existing)
                        continue
                    custom_objects.append(EmotionCustom.objects.create(
                        profil=profil,
                        libelle=cleaned_value
                    ))
                if custom_objects:
                    reve.emotions_custom.set(custom_objects)

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

class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


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


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()

        return HttpResponseRedirect(
            reverse("polls:results", args=(question.id,))
        )


class QuestionnaireView(View):
    """
    Vue pour gérer le questionnaire sur les rêves
    Affiche le formulaire et traite la soumission
    """
    template_name = "polls/questionnaire.html"
    
    def get(self, request):
        """Afficher le formulaire de questionnaire"""
        form = QuestionnaireForm()
        # Passer l'état de connexion au template
        context = {
            'form': form,
            'is_authenticated': request.user.is_authenticated
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Traiter la soumission du questionnaire"""
        # Vérifier si l'utilisateur est connecté
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour soumettre le questionnaire.")
            return HttpResponseRedirect(reverse("login"))
        
        form = QuestionnaireForm(request.POST)
        
        if form.is_valid():
            questionnaire = form.save(commit=False)
            questionnaire.profil = request.user.profil
            questionnaire.save()
            
            messages.success(request, "Merci d'avoir complété le questionnaire ! Vos réponses ont été enregistrées.")
            return HttpResponseRedirect(reverse("polls:profil"))
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
            context = {
                'form': form,
                'is_authenticated': request.user.is_authenticated
            }
            return render(request, self.template_name, context)

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
                    return redirect('polls:questionnaire')
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