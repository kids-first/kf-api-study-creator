import pytz
import factory
from creator.data_templates.models import DataTemplate
from creator.users.factories import UserFactory
from creator.organizations.factories import OrganizationFactory


class DataTemplateFactory(factory.DjangoModelFactory):
    class Meta:
        model = DataTemplate

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    name = factory.Faker("name")
    icon = factory.fuzzy.FuzzyChoice(["file-alt", "ambulance", "syringe"])
    description = factory.Faker("paragraph", nb_sentences=3)
    creator = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
