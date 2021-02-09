import pytz
import factory
from django.contrib.auth import get_user_model
from creator.data_reviews.models import DataReview
from creator.users.factories import UserFactory

User = get_user_model()


class DataReviewFactory(factory.DjangoModelFactory):
    class Meta:
        model = DataReview

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    creator = factory.SubFactory(UserFactory)
