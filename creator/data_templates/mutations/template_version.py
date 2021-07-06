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


def check_templates(template_node_ids):
    """
    Check if the template_versions exist and return the TemplateVersion
    objects if they all exist. Helper function called in add/remove templates
    to studies mutations.
    """
    template_ids = []
    for tid in template_node_ids:
        _, temp_id = from_global_id(tid)
        template_ids.append(temp_id)

    # Check all template_versions exist
    temps = TemplateVersion.objects.filter(pk__in=template_ids).only("kf_id").all()
    if len(temps) != len(template_ids):
        raise GraphQLError(
            "Failed to add/remove template versions from studies because one "
            "or more template_versions in the input do not exist. "
        )
    return temps


class AddTemplatesToStudiesInput(graphene.InputObjectType):
    """
    Parameters used when adding template_versions to studies.
    """

    template_versions = graphene.List(
        graphene.ID,
        required=True,
        description="The template_versions to add to studies",
    )
    studies = graphene.List(
        graphene.ID,
        required=True,
        description="The studies the template_versions should be added to",
    )


class AddTemplatesToStudiesMutation(graphene.Mutation):
    """
    Mutation to add template_versions to studies.
    """

    class Arguments:
        input = AddTemplatesToStudiesInput(
            required=True,
            description="Arguments for adding the template_versions",
        )

    def mutate(self, info, input):
        """
        Update the studies of the template_versions.
        """
        user = info.context.user
        # Check that user can make changes to studies and templates
        if not user.has_perm("studies.change_study"):
            raise GraphQLError("Not allowed.")
        if not user.has_perm("data_templates.change_datatemplate"):
            raise GraphQLError("Not allowed.")

        studies = check_studies(input["studies"])
        for study in studies:
            if not user.studies.filter(kf_id=study.kf_id).exists():
                raise GraphQLError(
                    f"Not allowed - user is not a member of study "
                    f"{study.kf_id}. "
                )

        template_versions = check_templates(input["template_versions"])
        # Need to check permissions for each template, so loop through
        for template_version in template_versions:
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

            # User may only update a template version if it is not already
            # being used in any studies
            if template_version.released:
                raise GraphQLError(
                    "Not allowed - may only update templates that are not "
                    "being used by any studies"
                )

            template_version.studies.set(studies)
            template_version.save()

        return AddTemplatesToStudiesMutation(
            template_versions=template_versions
        )


class CreateTemplateVersionInput(graphene.InputObjectType):
    """Parameters used when creating a new template_version"""

    description = graphene.String(
        required=True, description="The description of the template_version"
    )
    field_definitions = graphene.JSONString(
        required=True, description="The field definitions for this template"
    )
    data_template = graphene.ID(
        required=True,
        description="The data_template that this template_version belongs to",
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
