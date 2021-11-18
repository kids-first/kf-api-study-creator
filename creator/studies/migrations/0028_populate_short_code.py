from django.db import migrations
import pandas as pd
import os

"""
Populate the newly-created short_code attribute of the Study model with
data from a spreadsheet created by DevOps which lives in this migration
folder.
"""


def set_short_code(apps, schema_editor):
    """
    Populate short_code for all Study objects using the provided data.
    """
    df = pd.read_csv(
        os.path.abspath("creator/studies/migrations/study_metadata.csv")
    )
    short_codes = pd.Series(df.code.values, index=df.kf_id).to_dict()
    Study = apps.get_model("studies", "Study")
    for study in Study.objects.all():
        kf_id = study.kf_id
        if kf_id in short_codes:
            study.short_code = short_codes[kf_id].strip()
        else:
            study.short_code = kf_id.replace("_", "")
        study.save()


def undo_set_short_code(apps, schema):
    """
    Set short_code to PLACEHOLDER for all Study objects.
    """
    Study = apps.get_model("studies", "Study")
    for study in Study.objects.all():
        study.short_code = "PLACEHOLDER"
        study.save()


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0027_add_short_code'),
    ]

    operations = [
        migrations.RunPython(set_short_code, reverse_code=undo_set_short_code),
    ]
