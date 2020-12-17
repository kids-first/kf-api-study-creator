import pytz
import factory
import factory.fuzzy
from creator.status.banners.models import Banner
from creator.users.factories import UserFactory


class BannerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Banner

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    creator = factory.SubFactory(UserFactory)
    start_date = factory.Faker(
        "date_time_between", start_date="-2y", end_date="-1y", tzinfo=pytz.UTC
    )
    end_date = factory.Faker(
        "date_time_between", start_date="-1m", end_date="now", tzinfo=pytz.UTC
    )
    enabled = factory.fuzzy.FuzzyChoice([True, False])
    message = factory.Faker("sentence")
    severity = factory.fuzzy.FuzzyChoice(
        [code for code, _ in Banner.SEVERITY_CHOICES]
    )
    url = factory.Faker("url")
    url_label = factory.Faker("sentence")
