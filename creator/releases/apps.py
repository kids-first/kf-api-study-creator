from django.apps import AppConfig


class ReleasesConfig(AppConfig):
    name = "creator.releases"

    def ready(self):
        import creator.releases.signals
