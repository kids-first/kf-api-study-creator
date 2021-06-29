# Generated by Django 2.2.20 on 2021-05-13 15:15

from django.db import migrations, models
import django.db.models.deletion


def set_default_org(apps, schema_editor):
    """
    Put all existing buckets under the default organizaton
    """
    Organization = apps.get_model("organizations", "Organization")
    Bucket = apps.get_model("buckets", "Bucket")
    org = Organization.objects.filter(name="Default Organization").first()

    for bucket in Bucket.objects.all().iterator():
        bucket.organization_id = org.pk
        bucket.save()


def delete_default_org(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
        ("buckets", "0002_add_custom_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="bucket",
            name="organization",
            field=models.ForeignKey(
                default=1,
                help_text="Organization this bucket belongs to",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="buckets",
                to="organizations.Organization",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(set_default_org, delete_default_org),
    ]