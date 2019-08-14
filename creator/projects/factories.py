import pytz
import factory
import random
from .models import Project, WORKFLOW_TYPES


class ProjectFactory(factory.DjangoModelFactory):
    class Meta:
        model = Project

    project_id = factory.Faker("slug")
    name = factory.Faker("bs")
    description = factory.Faker("bs")
    project_type = factory.LazyFunction(lambda: random.choice(["HAR", "DEL"]))
    workflow_type = factory.LazyFunction(
        lambda: random.choice([workflow[0] for workflow in WORKFLOW_TYPES])
    )
    created_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    modified_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    url = factory.Faker("url")
    created_by = factory.Faker("email")
