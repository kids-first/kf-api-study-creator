# Generated by Django 2.2.24 on 2021-09-10 21:07
"""
This migration does 2 things:
    - Attempt to reverse the migration 0024_set_old_types_to_oth which changed
    files with file type SHM and CLN to OTH
    - Attempt to change the file type of all files marked as OTH to something
    more specific
"""

from django.db import migrations, models
import pandas
import os


def set_file_type(apps, schema_editor):
    """
    Try our best to set files with file_type OTH to a more specific file type
    based on the file name
    """
    # Read corrections
    df = pandas.read_csv(
        os.path.abspath(
            "creator/files/migrations/file_type_corrections.csv"
        )
    )
    corrections = pandas.Series(
        df.file_type.values, index=df.kf_id
    ).to_dict()

    def other_to_specific_file_type(file):
        mappings = {
            "CLN": {
                "clinical",
                "participant",
                "subject",
                "phenotyp",
                "term coding",
                "demographic",
                "diagnos",
                "abnormalities",
            },
            "BSM": {"specimen", "sample", "shipping", "shipment"},
            "SEQ": {"sequencing", "harmoniz"},
            "FAM": {"family", "pedigree", "trio", "relationship", "peddy"},
        }
        for ft, words in mappings.items():
            if any(w in file.name.lower() for w in words):
                return ft
        return file.file_type

    # Get files with OTH file type, try setting to more specific type
    File = apps.get_model("files", "File")
    for f in File.objects.filter(file_type="OTH").all().iterator():
        if f.kf_id in corrections:
            ft = corrections[f.kf_id].upper()
        else:
            ft = other_to_specific_file_type(f)
        if ft != f.file_type:
            print(f"Updating file {f.kf_id} file_type {f.file_type} -> {ft}")
            f.file_type = ft
            f.save()


def undo_set_file_type(apps, schema_editor):
    """
    Change file type back to OTH for files that use new file types that were
    not there before this migration
    """
    File = apps.get_model("files", "File")
    db_alias = schema_editor.connection.alias
    ftypes = ["BSM", "CLN"]
    File.objects.using(db_alias).filter(file_type__in=ftypes).update(
        file_type="OTH"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("files", "0026_add_template_version"),
    ]
    operations = [
        migrations.AlterField(
            model_name="file",
            name="file_type",
            field=models.CharField(
                choices=[
                    ("OTH", "OTH"),
                    ("DBG", "DBG"),
                    ("BSM", "BSM"),
                    ("CLN", "CLN"),
                    ("SEQ", "SEQ"),
                    ("FAM", "FAM"),
                    ("FCM", "FCM"),
                    ("FTR", "FTR"),
                    ("PDA", "PDA"),
                    ("GOB", "GOB"),
                    ("PTD", "PTD"),
                    ("PTP", "PTP"),
                    ("ALM", "ALM"),
                    ("BBM", "BBM"),
                    ("BCM", "BCM"),
                    ("S3S", "S3S"),
                    ("GWO", "GWO"),
                ],
                default="OTH",
                max_length=3,
            ),
        ),
        migrations.RunPython(set_file_type, reverse_code=undo_set_file_type),
    ]