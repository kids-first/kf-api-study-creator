from pprint import pprint
import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id
from django.db import transaction
from django.conf import settings

from creator.studies.models import Study
from creator.data_templates.models import (
    DataTemplate,
    TemplateVersion,
)
from creator.data_templates.nodes.template_version import TemplateVersionNode


def check_studies(study_node_ids):
    """
    Check if studies exist and return the Study objects if all studies exist

    Helper function called in create/update template version mutations
    """
    # Convert graphql relay ids to primary keys
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
    """ Parameters used when creating a new template_version """

    description = graphene.String(
        required=True, description="The description of the template_version"
    )
    field_definitions = graphene.JSONString(
        required=True,
        description="The field definitions for this template"
    )
    data_template = graphene.ID(
        required=True,
        description="The data_template that this template_version belongs to"
    )
    studies = graphene.List(
        graphene.ID,
        description="The studies this template version should be assigned to"
    )


class UpdateTemplateVersionInput(graphene.InputObjectType):
    """ Parameters used when updating an existing template_version """

    description = graphene.String(
        description="The description of the template_version"
    )
    field_definitions = graphene.JSONString(
        description="The field definitions for this template"
    )
    studies = graphene.List(
        graphene.ID,
        description="The studies this template version should be assigned to"
    )


class CreateTemplateVersionMutation(graphene.Mutation):
    """ Creates a new template_version """

    class Arguments:
        input = CreateTemplateVersionInput(
            required=True, description="Attributes for the new template_version"
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
        model, node_id = from_global_id(dt_id)

        try:
            dt = DataTemplate.objects.get(pk=node_id)
        except DataTemplate.DoesNotExist:
            raise GraphQLError(f"DataTemplate {node_id} does not exist")

        # User may only add template versions to a template owned by their org
        if not user.organizations.filter(pk=dt.organization.pk).exists():
            raise GraphQLError(
                "Not allowed - may only add template versions to templates "
                "that are owned by the user's organization."
            )

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
            if study_ids:
                # Ensure studies exist
                studies = check_studies(study_ids)
                template_version.studies.set(studies)
                template_version.save()

        return CreateTemplateVersionMutation(template_version=template_version)


class UpdateTemplateVersionMutation(graphene.Mutation):
    """ Update an existing template_version """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the template_version to update"
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

        model, node_id = from_global_id(id)

        try:
            template_version = TemplateVersion.objects.get(id=node_id)
        except TemplateVersion.DoesNotExist:
            raise GraphQLError(f"TemplateVersion {node_id} does not exist")

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

        # User may only update a template version if it is not already being
        # used in any studies
        if template_version.released:
            raise GraphQLError(
                "Not allowed - may only update templates that are not being "
                "used by any studies"
            )

        # Get study ids for later
        study_ids = input.pop("studies", None)

        with transaction.atomic():
            for k, v in input.items():
                setattr(template_version, k, v)
            template_version.creator = user

            # Validate and save template
            template_version.clean()
            template_version.save()

            # Update studies if they exist
            if study_ids:
                studies = check_studies(study_ids)
                template_version.studies.set(studies)
                template_version.save()

        return UpdateTemplateVersionMutation(template_version=template_version)


class Mutation:
    """ Mutations for template_versions """

    create_template_version = CreateTemplateVersionMutation.Field(
        description="Create a new template_version."
    )
    update_template_version = UpdateTemplateVersionMutation.Field(
        description="Update a given template_version"
    )
