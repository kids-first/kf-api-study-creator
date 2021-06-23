import pytz
import factory
from creator.data_templates.models import DataTemplate, TemplateVersion
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


class TemplateVersionFactory(factory.DjangoModelFactory):
    class Meta:
        model = TemplateVersion

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    description = factory.Faker("paragraph", nb_sentences=3)
    field_definitions = factory.Dict(
        {
            "fields": [
                {
                    "key": f"key_{x}",
                    "label": f"label_{x}",
                    "description": f"My field label_{x} is awesome",
                    "required": "required",
                    "default": "foo",
                    "data_type": "string",
                    "instructions": f"Populate label_{x} properly",
                    "accepted_values": None,
                }
                for x in range(2)
            ]
        }
    )
    creator = factory.SubFactory(UserFactory)
    data_template = factory.SubFactory(DataTemplateFactory)

    @factory.post_generation
    def studies(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.studies.set(extracted)
