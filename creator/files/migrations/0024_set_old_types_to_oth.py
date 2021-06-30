from django.db import migrations
from creator.files.models import FileType


def forwards_func(apps, schema_editor):
    File = apps.get_model("files", "File")
    db_alias = schema_editor.connection.alias
    # These will be deleted in a future commit, should probably hard-code
    old_types = ["SHM", "CLN"]
    File.objects.using(db_alias).filter(file_type__in=old_types).update(
        file_type=FileType.OTH.value
    )


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0023_add_document_types"),
    ]

    operations = [
        migrations.RunPython(
            forwards_func, reverse_code=migrations.RunPython.noop
        )
    ]
