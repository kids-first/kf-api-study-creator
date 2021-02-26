from django.apps import AppConfig


class DataReviewsConfig(AppConfig):
    name = "creator.data_reviews"

    def ready(self):
        import creator.data_reviews.signals
