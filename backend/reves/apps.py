from django.apps import AppConfig


class RevesConfig(AppConfig):
    name = 'reves'
    label = 'polls'

    def ready(self):
        import reves.signals
