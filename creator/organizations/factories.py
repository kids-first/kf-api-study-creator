import pytz
import factory
from creator.organizations.models import Organization


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
