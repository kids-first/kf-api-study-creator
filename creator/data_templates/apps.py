from django.apps import AppConfig


class DataTemplatesConfig(AppConfig):
    name = "creator.data_templates"

    def ready(self):
        import creator.data_templates.signals
