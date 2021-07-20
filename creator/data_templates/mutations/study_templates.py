import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.studies.nodes import StudyNode
from creator.data_templates.models import TemplateVersion
from creator.data_templates.nodes.template_version import TemplateVersionNode
from creator.data_templates.mutations.template_version import check_studies


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
    templates = TemplateVersion.objects.filter(pk__in=template_ids).all()
    if len(templates) != len(template_ids):
        raise GraphQLError(
            "Failed to add/remove template versions from studies because one "
            "or more template_versions in the input do not exist. "
        )
    return templates


class TemplatesStudiesInput(graphene.InputObjectType):
    """
    Parameters used when adding/removing template_versions to/from studies.
    """

    template_versions = graphene.List(
        graphene.ID,
        required=True,
        description="The template_versions to add/remove to/from the studies",
    )
    studies = graphene.List(
        graphene.ID,
        required=True,
        description=(
            "The studies the template_versions should be added/removed to/from"
        ),
    )


class AddTemplatesToStudiesMutation(graphene.Mutation):
    """
    Mutation to add template_versions to studies.
    """

    class Arguments:
        input = TemplatesStudiesInput(
            required=True,
            description="Arguments for adding the template_versions",
        )

    success = graphene.Boolean()
    studies = graphene.List(StudyNode)
    template_versions = graphene.List(TemplateVersionNode)

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

        studies = check_studies(input["studies"], user)

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

            template_version.studies.add(*studies)
            template_version.save()

        return AddTemplatesToStudiesMutation(
            success=True, studies=studies, template_versions=template_versions
        )


class RemoveTemplatesFromStudiesMutation(graphene.Mutation):
    """
    Mutation to remove template_versions from studies.
    """

    class Arguments:
        input = TemplatesStudiesInput(
            required=True,
            description="Arguments for removing the template_versions",
        )

    success = graphene.Boolean()
    studies = graphene.List(StudyNode)
    template_versions = graphene.List(TemplateVersionNode)

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

        studies = check_studies(input["studies"], user)

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

            template_version.studies.remove(*studies)
            template_version.save()

        return RemoveTemplatesFromStudiesMutation(
            success=True, studies=studies, template_versions=template_versions
        )


class Mutation:
    """Mutations for template_version study operations"""

    add_templates_to_studies = AddTemplatesToStudiesMutation.Field(
        description="Add given template_versions to given studies"
    )
    remove_templates_from_studies = RemoveTemplatesFromStudiesMutation.Field(
        description="Remove given template_versions from given studies"
    )
