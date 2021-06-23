import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id
from django.conf import settings

from creator.organizations.models import Organization
from creator.data_templates.models import DataTemplate
from creator.data_templates.nodes.data_template import DataTemplateNode


class CreateDataTemplateInput(graphene.InputObjectType):
    """Parameters used when creating a new data_template"""

    name = graphene.String(
        required=True, description="The name of the data_template"
    )
    description = graphene.String(
        required=True, description="The description of the data_template"
    )
    icon = graphene.String(
        description="Name of the Font Awesome icon to use when displaying the "
        "template"
    )
    organization = graphene.ID(
        required=True,
        description="The organization that will own this data_template",
    )


class UpdateDataTemplateInput(graphene.InputObjectType):
    """Parameters used when updating an existing data_template"""

    name = graphene.String(description="The name of the data_template")
    description = graphene.String(
        description="The description of the data_template"
    )
    icon = graphene.String(
        description="Name of the Font Awesome icon to use when displaying the "
        "template"
    )
    organization = graphene.ID(
        description="The organization that will own this data_template"
    )


class CreateDataTemplateMutation(graphene.Mutation):
    """Creates a new data_template"""

    class Arguments:
        input = CreateDataTemplateInput(
            required=True, description="Attributes for the new data_template"
        )

    data_template = graphene.Field(DataTemplateNode)

    def mutate(self, info, input):
        """
        Creates a new data_template.
        """
        user = info.context.user
        if not user.has_perm("data_templates.add_datatemplate"):
            raise GraphQLError("Not allowed")

        # Check if organization exists
        org_id = input.pop("organization")
        model, org_id = from_global_id(org_id)

        try:
            org = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            raise GraphQLError(f"Organization {org_id} does not exist")

        # User may only add templates to an org they are a member of
        if not user.organizations.filter(pk=org.pk).exists():
            raise GraphQLError(
                "Not allowed - may only add templates to an organization the "
                "user is a member of."
            )

        # Create data template
        data_template = DataTemplate(**{k: input[k] for k in input})
        data_template.organization = org
        data_template.creator = user
        data_template.save()

        return CreateDataTemplateMutation(data_template=data_template)


class UpdateDataTemplateMutation(graphene.Mutation):
    """Update an existing data_template"""

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the data_template to update"
        )
        input = UpdateDataTemplateInput(
            required=True, description="Attributes for the data_template"
        )

    data_template = graphene.Field(DataTemplateNode)

    def mutate(self, info, id, input):
        """
        Updates an existing data_template
        """
        user = info.context.user
        if not user.has_perm("data_templates.change_datatemplate"):
            raise GraphQLError("Not allowed")

        model, dt_id = from_global_id(id)

        try:
            data_template = DataTemplate.objects.get(id=dt_id)
        except DataTemplate.DoesNotExist:
            raise GraphQLError(f"DataTemplate {dt_id} does not exist")

        # User may only change templates for an org they are a member of
        if not (
            user.organizations.filter(
                pk=data_template.organization.pk
            ).exists()
        ):
            raise GraphQLError(
                "Not allowed - may only update templates owned by an "
                "organization that the user is a member of"
            )

        # User may only update a template if it is not being used in
        # any studies
        if data_template.released:
            raise GraphQLError(
                "Not allowed - may only update templates that are not being "
                "used by any studies"
            )

        # Save org id for later
        org_id = input.pop("organization", None)

        # Update data template
        for k, v in input.items():
            setattr(data_template, k, v)

        # Check if organization exists
        if org_id:
            model, org_id = from_global_id(org_id)
            try:
                org = Organization.objects.get(pk=org_id)
            except Organization.DoesNotExist:
                raise GraphQLError(f"Organization {org_id} does not exist")
            data_template.organization = org

        data_template.save()

        return UpdateDataTemplateMutation(data_template=data_template)


class DeleteDataTemplateMutation(graphene.Mutation):
    """Delete an existing data_template"""

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the data_template to delete"
        )

    success = graphene.Boolean()
    id = graphene.String()

    def mutate(self, info, id):
        """
        Deletes an existing data_template
        """
        user = info.context.user
        if not user.has_perm("data_templates.delete_datatemplate"):
            raise GraphQLError("Not allowed")

        model, dt_id = from_global_id(id)

        try:
            data_template = DataTemplate.objects.get(id=dt_id)
        except DataTemplate.DoesNotExist:
            raise GraphQLError(f"DataTemplate {dt_id} does not exist")

        # User may only delete templates for an org they are a member of
        if not (
            user.organizations.filter(
                pk=data_template.organization.pk
            ).exists()
        ):
            raise GraphQLError(
                "Not allowed - may only delete templates that are owned by "
                "organizations that the user is a member of"
            )

        # User may only delete templates that are not being used in any studies
        if data_template.released:
            raise GraphQLError(
                "Not allowed - may only delete templates that are not being "
                "used by any studies"
            )

        data_template.delete()

        return DeleteDataTemplateMutation(success=True, id=id)


class Mutation:
    """Mutations for data_templates"""

    create_data_template = CreateDataTemplateMutation.Field(
        description="Create a new data_template."
    )
    update_data_template = UpdateDataTemplateMutation.Field(
        description="Update a given data_template"
    )
    delete_data_template = DeleteDataTemplateMutation.Field(
        description="Delete a given data_template"
    )
