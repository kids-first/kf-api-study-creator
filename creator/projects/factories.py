import pytz
import factory.fuzzy
from faker.providers import BaseProvider
from .models import Project, WORKFLOW_TYPES


class TypeProvider(BaseProvider):
    def project_type(self):
        return factory.fuzzy.FuzzyChoice(["HAR", "DEL", "RES"]).fuzz()

    def workflow_type(self):
        return factory.fuzzy.FuzzyChoice([w[0] for w in WORKFLOW_TYPES]).fuzz()


factory.Faker.add_provider(TypeProvider)


class ProjectFactory(factory.DjangoModelFactory):
    class Meta:
        model = Project

    project_id = factory.Faker("slug")
    name = factory.Faker("bs")
    description = factory.Faker("bs")
    project_type = factory.Faker("project_type")
    workflow_type = factory.Faker("workflow_type")
    created_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    modified_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    url = factory.Faker("url")
    created_by = factory.Faker("email")
