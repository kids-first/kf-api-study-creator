from django.apps import AppConfig


class IngestRunsConfig(AppConfig):
    name = "creator.ingest_runs"

    def ready(self):
        import creator.ingest_runs.signals  # noqa
