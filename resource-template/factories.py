import pytz
from creator.{{ app_name}}.models import {{ model_name }}


class {{ model_name }}Factory(factory.DjangoModelFactory):
    class Meta:
        model = {{ model_name }}

    created_at = factory.Faker(
        "date_time_between", start_date="-2y", end_date="now", tzinfo=pytz.UTC
    )
