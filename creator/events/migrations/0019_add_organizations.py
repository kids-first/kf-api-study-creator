# Generated by Django 2.2.20 on 2021-05-13 13:51

from django.db import migrations, models
import django.db.models.deletion


def set_default_org(apps, schema_editor):
    """
    Put all existing events under the default organizaton
    """
    Organization = apps.get_model("organizations", "Organization")
    Event = apps.get_model("events", "Event")
    org = Organization.objects.filter(name="Default Organization").first()

    for event in Event.objects.all().iterator():
        event.organization_id = org.pk
        event.save()


def delete_default_org(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
        ("events", "0018_add_intermed_ingest_process_states"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="organization",
            field=models.ForeignKey(
                null=True,
                help_text="Organization related to this event",
                on_delete=django.db.models.deletion.CASCADE,
                to="organizations.Organization",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(set_default_org, delete_default_org),
        migrations.AlterField(
            model_name="event",
            name="organization",
            field=models.ForeignKey(
                null=False,
                help_text="Organization related to this event",
                on_delete=django.db.models.deletion.CASCADE,
                to="organizations.Organization",
            ),
            preserve_default=False,
        ),
    ]
