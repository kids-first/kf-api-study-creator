import pytz
import factory
from creator.organizations.models import Organization
from creator.studies.factories import StudyFactory


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Organization
        django_get_or_create = ("name",)

    name = factory.Faker("bs")
    created_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return

        # A list of members were passed to be added to the organization
        if extracted:
            self.members.set(extracted)

    @factory.post_generation
    def studies(self, create, extracted, **kwargs):
        """
        After an organization is created with the factory, generate _extracted_
        related Studies. If _extracted_ is not provided, default to
        _DEFAULT_NUM_.
        """
        if not create:
            return
        DEFAULT_NUM = 2
        extracted = DEFAULT_NUM if extracted is None else extracted
        if extracted:
            StudyFactory.create_batch(extracted, organization=self)
