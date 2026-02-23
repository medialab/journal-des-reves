from django.db.models import F
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, JsonResponse, FileResponse
from django.urls import reverse
from django.contrib import messages
from django.views import generic, View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
import uuid
import os

from .models import Choice, Question, Reve, Profil
from .services.journal_service import get_journal_data
from .forms import ReveForm


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
            **journal_data
        }

        return render(request, "polls/profil.html", context)

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
    Vue pour enregistrer un nouveau rêve avec audio et transcription
    Support pour upload AJAX d'audio WAV depuis le navigateur
    """

    def get(self, request):
        """Afficher la page d'enregistrement"""
        context = {"title": "Enregistrer un rêve"}
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
            audio_file = request.FILES.get('audio_file')
            intensite = request.POST.get('intensite', '5')
            transcription = request.POST.get('transcription', '').strip()

            # Validation
            if not audio_file:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun fichier audio fourni'
                }, status=400)

            # Valider le fichier audio
            if not audio_file.name.endswith('.wav'):
                audio_file.name = f'{uuid.uuid4()}.wav'

            # Valider l'intensité
            try:
                intensite = int(intensite)
                if intensite < 1 or intensite > 10:
                    intensite = 5
            except (ValueError, TypeError):
                intensite = 5

            # Créer le rêve
            reve = Reve.objects.create(
                profil=profil,
                audio=audio_file,
                intensite=intensite,
                transcription=transcription if transcription else None
            )

            messages.success(request, 'Votre rêve a été enregistré avec succès!')
            
            return JsonResponse({
                'success': True,
                'message': 'Rêve enregistré',
                'reve_id': reve.id,
                'redirect_url': reverse('polls:journal')
            })

        except Exception as error:
            print(f'❌ Erreur enregistrement rêve: {error}')
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
            **journal_data
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