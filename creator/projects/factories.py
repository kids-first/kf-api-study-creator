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
    project_type = factory.LazyFunction(
        lambda: factory.fuzzy.FuzzyChoice(["HAR", "DEL"])
    )
    workflow_type = factory.LazyFunction(
        lambda: factory.fuzzy.FuzzyChoice(WORFLOW_TYPES, getter=lambda c: c[0])
    )
    created_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    modified_on = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
    url = factory.Faker("url")
    created_by = factory.Faker("email")
