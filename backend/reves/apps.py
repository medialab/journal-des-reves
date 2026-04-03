from django.apps import AppConfig


class RevesConfig(AppConfig):
    name = 'reves'
    label = 'reves'

    def ready(self):
        import reves.signals
