import logging

import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id
from graphene_file_upload.scalars import Upload
from django.db import transaction
from django.conf import settings
from kf_lib_data_ingest.common.io import read_df
from marshmallow import ValidationError

from creator.studies.models import Study
from creator.data_templates.models import (
    DataTemplate,
    TemplateVersion,
)
from creator.data_templates.nodes.template_version import TemplateVersionNode

logger = logging.getLogger(__name__)


def check_studies(study_ids, user, primary_keys=False):
    """
    Check if user is allowed to modify all studies and studies exist.
    Return the Study objects if checks pass
    Helper function called in create/update template version mutations
    """
    # Check that user is allowed to modify studies
    if not user.has_perm("studies.change_study"):
        raise GraphQLError(
            "Not allowed - user not authorized to modify studies"
        )

    # Empty list
    if len(study_ids) == 0:
        return study_ids

    # Convert graphql relay ids to primary keys
    if not primary_keys:
        study_node_ids = study_ids
        study_ids = []
        for sid in study_node_ids:
            _, study_id = from_global_id(sid)
            study_ids.append(study_id)

    # Check all studies exist
    studies = Study.objects.filter(pk__in=study_ids).only("kf_id").all()
    if len(studies) != len(study_ids):
        raise GraphQLError(
            "Failed to create/update template version because one or more "
            "studies in the input do not exist. "
        )

    return studies


class CreateTemplateVersionInput(graphene.InputObjectType):
    """Parameters used when creating a new template_version"""

    description = graphene.String(
        required=True,
        description="The description of the template_version",
    )
    field_definitions = graphene.JSONString(
        required=True,
        description="The field definitions for this template",
    )
    data_template = graphene.ID(
        required=True,
        description="The data_template that this template_version belongs to",
    )
    apply_to_all = graphene.Boolean(
        description="Whether to add this template version to all of the "
        "organization's studies. This will override anything in the studies "
        "input parameter.",
    )
    studies = graphene.List(
        graphene.ID,
        description="The studies this template version should be assigned to",
    )


class UpdateTemplateVersionInput(graphene.InputObjectType):
    """Parameters used when updating an existing template_version"""

    description = graphene.String(
        description="The description of the template_version"
    )
    field_definitions = graphene.JSONString(
        description="The field definitions for this template"
    )
    apply_to_all = graphene.Boolean(
        description="Whether to add this template version to all of the "
        "organization's studies. This will override anything in the studies "
        "input parameter.",
    )
    studies = graphene.List(
        graphene.ID,
        description="The studies this template version should be assigned to",
    )


class CreateTemplateVersionMutation(graphene.Mutation):
    """Creates a new template_version"""

    class Arguments:
        input = CreateTemplateVersionInput(
            required=True,
            description="Attributes for the new template_version",
        )

    template_version = graphene.Field(TemplateVersionNode)

    def mutate(self, info, input):
        """
        Creates a new template_version.
        """
        user = info.context.user
        if not user.has_perm("data_templates.add_datatemplate"):
            raise GraphQLError("Not allowed")

        # Check if data template exists
        dt_id = input.pop("data_template")
        model, dt_id = from_global_id(dt_id)

        try:
            dt = DataTemplate.objects.get(pk=dt_id)
        except DataTemplate.DoesNotExist:
            raise GraphQLError(f"DataTemplate {dt_id} does not exist")

        # User may only add template versions to a template owned by their org
        if not user.organizations.filter(pk=dt.organization.pk).exists():
            raise GraphQLError(
                "Not allowed - may only add template versions to templates "
                "that are owned by the user's organization."
            )

        # Get apply flag for later
        apply_to_all = input.pop("apply_to_all", None)

        # Get study ids for later
        study_ids = input.pop("studies", None)

        # Create template version
        with transaction.atomic():
            template_version = TemplateVersion(**{k: input[k] for k in input})
            template_version.creator = user
            template_version.data_template = dt

            # Validate and save template
            template_version.clean()
            template_version.save()

            # Add studies to the template version if they exist
            if apply_to_all:
                study_ids = [s.pk for s in dt.organization.studies.all()]
                studies = check_studies(study_ids, user, primary_keys=True)
                template_version.studies.set(studies)

            # Add template version to selected studies if they exist
            else:
                if study_ids:
                    studies = check_studies(study_ids, user)
                    template_version.studies.set(studies)
            template_version.save()

        return CreateTemplateVersionMutation(template_version=template_version)


class UpdateTemplateVersionMutation(graphene.Mutation):
    """Update an existing template_version"""

    class Arguments:
        id = graphene.ID(
            required=True,
            description="The ID of the template_version to update",
        )
        input = UpdateTemplateVersionInput(
            required=True, description="Attributes for the template_version"
        )

    template_version = graphene.Field(TemplateVersionNode)

    def mutate(self, info, id, input):
        """
        Updates an existing template_version
        """
        user = info.context.user
        if not user.has_perm("data_templates.change_datatemplate"):
            raise GraphQLError("Not allowed")

        model, tv_id = from_global_id(id)

        try:
            template_version = TemplateVersion.objects.get(id=tv_id)
        except TemplateVersion.DoesNotExist:
            raise GraphQLError(f"TemplateVersion {tv_id} does not exist")

        # User may only update template versions owned by their org
        if not (
            user.organizations.filter(
                pk=template_version.organization.pk
            ).exists()
        ):
            raise GraphQLError(
                "Not allowed - may only update template versions for "
                "templates that are owned by the user's organization."
            )

        # Get apply flag for later
        apply_to_all = input.pop("apply_to_all", None)

        # Get study ids for later
        study_ids = input.pop("studies", None)

        with transaction.atomic():
            for k, v in input.items():
                setattr(template_version, k, v)
            template_version.creator = user

            # Validate template
            template_version.clean()

            # Add studies to the template version if they exist
            if apply_to_all:
                dt = template_version.data_template
                study_ids = [s.pk for s in dt.organization.studies.all()]
                studies = check_studies(study_ids, user, primary_keys=True)
                template_version.studies.set(studies)

            # Add template version to selected studies if they exist
            else:
                if study_ids is not None:
                    studies = check_studies(study_ids, user)
                    template_version.studies.set(studies)

            template_version.save()

        return UpdateTemplateVersionMutation(template_version=template_version)


class DeleteTemplateVersionMutation(graphene.Mutation):
    """Delete an existing template_version"""

    class Arguments:
        id = graphene.ID(
            required=True,
            description="The ID of the template_version to delete",
        )

    success = graphene.Boolean()
    id = graphene.String()

    def mutate(self, info, id):
        """
        Deletes an existing template_version
        """
        user = info.context.user
        if not user.has_perm("data_templates.delete_datatemplate"):
            raise GraphQLError("Not allowed")

        model, tv_id = from_global_id(id)

        try:
            template_version = TemplateVersion.objects.get(id=tv_id)
        except TemplateVersion.DoesNotExist:
            raise GraphQLError(f"TemplateVersion {tv_id} does not exist")

        # User may only delete templates for an org they are a member of
        if not (
            user.organizations.filter(
                pk=template_version.organization.pk
            ).exists()
        ):
            raise GraphQLError(
                "Not allowed - may only delete templates that are owned by "
                "organizations that the user is a member of"
            )

        # User may only delete templates that are not being used in any studies
        if template_version.released:
            raise GraphQLError(
                "Not allowed - may only delete templates that are not being "
                "used by any studies"
            )

        template_version.delete()

        return DeleteTemplateVersionMutation(success=True, id=id)


class UploadFieldDefinitionsMutation(graphene.Mutation):
    """Upload a template_version's field definitions from file"""

    class Arguments:
        file = Upload(
            required=True,
            description="The file containing template field definitions",
        )

    success = graphene.Boolean()
    file_name = graphene.String()
    file_size = graphene.Float()
    field_definitions = graphene.JSONString()

    def mutate(self, info, file):
        """
        Imports field definitions from a file (tsv, csv, xlsx, or json):

        - Parse file content into JSON
        - Best-effort clean up of human errors
        - Validate JSON against field definitions schema

        Returns the clean version of the field definitions as a JSON string
        or raises a ValidationError with a list of all errors found
        """
        user = info.context.user
        if not user.has_perm("data_templates.change_datatemplate"):
            raise GraphQLError("Not allowed")

        file_name = file.name
        file_size = file.size

        if file.size > settings.FILE_MAX_SIZE:
            raise GraphQLError(
                f"File size {file_size} exceeds max size: "
                f"{settings.FILE_MAX_SIZE}"
            )

        try:
            field_definitions = TemplateVersion.load_field_definitions(
                file, original_name=file.name
            )
        except ValidationError:
            raise
        except Exception as e:
            logger.exception(str(e))
            raise GraphQLError(
                "Something went wrong while importing field definitions"
            )

        return UploadFieldDefinitionsMutation(
            success=True,
            file_name=file_name,
            file_size=file_size,
            field_definitions=field_definitions
        )


class Mutation:
    """Mutations for template_versions"""

    create_template_version = CreateTemplateVersionMutation.Field(
        description="Create a new template_version."
    )
    update_template_version = UpdateTemplateVersionMutation.Field(
        description="Update a given template_version"
    )
    delete_template_version = DeleteTemplateVersionMutation.Field(
        description="Delete a given template_version"
    )
    upload_field_definitions = UploadFieldDefinitionsMutation.Field(
        description="Upload a template_version's field definitions from file"
    )
