from django.apps import AppConfig


class EventsConfig(AppConfig):
    name = "creator.events"

    def ready(self):
        import creator.events.signals
