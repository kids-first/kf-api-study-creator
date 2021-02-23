import pytz
import factory
from django.contrib.auth import get_user_model
from creator.users.factories import UserFactory
from creator.studies.factories import StudyFactory
from creator.data_reviews.models import DataReview, State

User = get_user_model()


class DataReviewFactory(factory.DjangoModelFactory):
    class Meta:
        model = DataReview

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    creator = factory.SubFactory(UserFactory)
    name = factory.Faker("name")
    description = factory.Faker("paragraph", nb_sentences=3)
    state = factory.fuzzy.FuzzyChoice(
        [
            attr
            for attr in dir(State)
            if not callable(getattr(State, attr)) and not attr.startswith("__")
        ]
    )
    study = factory.SubFactory(StudyFactory)

    @factory.post_generation
    def files(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.files.set(extracted)
