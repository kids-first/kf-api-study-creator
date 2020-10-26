import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from django.conf import settings
from creator.{{ app_name }}.nodes import {{ model_name }}Node
from creator.{{ app_name }}.models import {{ model_name }}


class Create{{ model_name }}Input(graphene.InputObjectType):
    """ Parameters used when creating a new {{ singular }} """

    name = graphene.String(description="The name of the {{ singular }}")


class Update{{ model_name }}Input(graphene.InputObjectType):
    """ Parameters used when updating an existing {{ singular }} """

    name = graphene.String(description="The name of the {{ singular }}")


class Create{{ model_name }}Mutation(graphene.Mutation):
    """ Creates a new {{ singular }} """

    class Arguments:
        input = Create{{ model_name }}Input(
            required=True, description="Attributes for the new {{ singular }}"
        )

    {{ singular }} = graphene.Field({{ model_name }}Node)

    def mutate(self, info, input):
        """
        Creates a new {{ singular }}.
        """
        user = info.context.user
        if not user.has_perm("{{ app_name }}.add_{{ permission_singular }}"):
            raise GraphQLError("Not allowed")

        {{ singular }} = {{ model_name}}()
        return Create{{ model_name }}Mutation({{ singular }}={{ singular }})


class Update{{ model_name }}Mutation(graphene.Mutation):
    """ Update an existing {{ singular }} """

    class Arguments:
        id = graphene.ID(
            required=True, description="The ID of the {{ singular }} to update"
        )
        input = Update{{ model_name }}Input(
            required=True, description="Attributes for the {{ singular }}"
        )

    {{ singular }} = graphene.Field({{ model_name }}Node)

    def mutate(self, info, id, input):
        """
        Updates an existing {{ singular }}
        """
        user = info.context.user
        if not user.has_perm("{{ app_name }}.change_{{ permission_singular }}"):
            raise GraphQLError("Not allowed")

        model, node_id = from_global_id(id)

        try:
            {{ singular }} = {{ model_name }}.objects.get(id=node_id)
        except {{ model_name }}.DoesNotExist:
            raise GraphQLError("{{ model_name }} was not found")

        return Update{{ model_name }}Mutation({{ singular }}={{ singular }})


class Mutation:
    """ Mutations for {{ plural }} """

    create_{{ singular }} = Create{{ model_name }}Mutation.Field(
        description="Create a new {{ singular }}."
    )
    update_{{ singular }} = Update{{ model_name }}Mutation.Field(
        description="Update a given {{ singular }}"
    )
