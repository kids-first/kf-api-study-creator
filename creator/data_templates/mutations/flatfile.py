from pprint import pprint
import logging
import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id
from django.conf import settings
from marshmallow import ValidationError

from creator.studies.models import Study
from creator.data_templates.default_templates import default_templates
from creator.data_templates.models import TemplateVersion
from creator.data_templates.flatfile_settings_schema import (
    FlatfileSettingsSchema
)

flatfile_schema = FlatfileSettingsSchema()
logger = logging.getLogger(__name__)


def check_templates(node_ids):
    """
    Check if all template versions exist
    """
    # Convert graphql relay ids to primary keys
    template_version_ids = []
    for nid in node_ids:
        _, template_version_id = from_global_id(nid)
        template_version_ids.append(template_version_id)

    # Check all template versions exist
    template_versions = TemplateVersion.objects.filter(
        pk__in=template_version_ids
    ).all()
    if len(template_versions) != len(node_ids):
        raise TemplateVersion.DoesNotExist(
            "One or more template versions in the input do not exist"
        )
    return template_versions


class CreateFlatfileSettingsMutation(graphene.Mutation):
    """
    Build settings object for the Flatfile import button from the
    template versions supplied
    """
    class Arguments:
        template_versions = graphene.List(
            graphene.ID,
            description="The templates that will be used to build the "
            "settings for the Flatfile import button"
        )

    flatfile_settings = graphene.JSONString(
        description="The Flatfile button import settings"
    )

    def mutate(self, info, template_versions=None):
        """
        Creates a Flatfile settings JSON object
        """
        user = info.context.user
        if not user.has_perm("data_templates.view_datatemplate"):
            raise GraphQLError("Not allowed")

        title = settings.FLATFILE_DEFAULT_TITLE
        import_type = settings.FLATFILE_DEFAULT_TYPE
        fields = []

        # Use templates if provided and it has templates
        if template_versions:
            template_versions = check_templates(template_versions)

            # Set import type
            if len(template_versions) == 1:
                template_name = template_versions[0].data_template.name
                import_type = f"{template_name} Data"

            title = f"Upload {import_type}"

            # Get fields from templates
            for t in template_versions:
                fields.extend(t.field_definitions["fields"])

        # Use default templates
        else:
            logger.info("Using default templates to build flatfile settings")
            for t in default_templates:
                fields.extend(t["fields"])

        # Convert templates to Flatfile settings
        try:
            flatfile_settings = flatfile_schema.load(
                {"fields": fields, "type": import_type, "title": title}
            )
        except ValidationError as e:
            raise
        except TemplateVersion.DoesNotExist as e:
            raise
        except Exception as e:
            msg = "Unable to build Flatfile button settings"
            logger.exception(f"{msg}. Caused by:\n{str(e)}")
            raise GraphQLError(msg)

        return CreateFlatfileSettingsMutation(
            flatfile_settings=flatfile_settings
        )


class Mutation:
    """Mutations for Flatfile integration"""

    create_flatfile_settings = CreateFlatfileSettingsMutation.Field(
        description="Convert template versions to a JSON Flatfile settings obj"
    )
