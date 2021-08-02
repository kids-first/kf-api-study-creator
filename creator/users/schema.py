import graphene
from graphene import relay
from graphql_relay import from_global_id
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from graphene_django.converter import convert_django_field_with_choices
from graphene_django.filter import DjangoFilterConnectionField

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from creator.studies.models import Membership
from creator.organizations.queries import OrganizationFilter
from creator.users.mutations import Mutation
from creator.users.queries import Query

User = get_user_model()


class CollaboratorConnection(graphene.Connection):
    class Meta:
        abstract = True

    class Edge:
        """
        Extends relay edges on study-collaborator relationships to include
        information from the 'Membership' through-table.
        """

        # Need to referrence the node by module to avoid circular deps
        invited_by = graphene.Field("creator.users.schema.UserNode")
        joined_on = graphene.DateTime()
        # We need to manually convert the role field's choices into enums
        # that graphene understands
        role = convert_django_field_with_choices(
            Membership._meta.get_field("role")
        )

        def resolve_invited_by(root, info, **kwargs):
            """
            Returns the user that invited this collaborator to the study.
            """
            study_id = root._get_study_id(info)
            invited_by = Membership.objects.get(
                collaborator=root.node.id, study=study_id
            ).invited_by

            return invited_by

        def resolve_joined_on(root, info, **kwargs):
            """
            Returns the date the collaborator joined the study.
            """
            study_id = root._get_study_id(info)
            joined_on = Membership.objects.get(
                collaborator=root.node.id, study=study_id
            ).joined_on

            return joined_on

        def resolve_role(root, info, **kwargs):
            """
            Returns the role of the collaborator in the study.
            """
            study_id = root._get_study_id(info)
            role = (
                Membership.objects.filter(
                    collaborator=root.node.id, study=study_id
                )
                .first()
                .role
            )

            return role

        def _get_study_id(self, info):
            """
            The study id for which the user is a collaborator may be passed
            in as either the 'id' variable or the 'study' variable depending on
            which query is being executed.
            This attempts to resolve both and asserts that the id decoded is
            the expected StudyNode type.
            """
            gid = info.variable_values.get(
                "study"
            ) or info.variable_values.get("id")
            node_type, study_id = from_global_id(gid)
            assert node_type == "StudyNode"
            return study_id


class UserNode(DjangoObjectType):
    display_name = graphene.String(source="display_name")

    organizations = DjangoFilterConnectionField(
        "creator.organizations.queries.OrganizationNode",
        filterset_class=OrganizationFilter,
        description="List all organizations the user is in",
    )

    class Meta:
        model = User
        interfaces = (relay.Node,)
        connection_class = CollaboratorConnection
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "last_login",
            "date_joined",
            "picture",
            "study_subscriptions",
            "slack_notify",
            "slack_member_id",
            "email_notify",
            "studies",
            "organizations",
            "groups",
        ]

    @classmethod
    def get_node(cls, info, sub):
        """
        Only return node if user is an admin or is self
        """
        try:
            obj = cls._meta.model.objects.get(sub=sub)
        except cls._meta.model.DoesNotExist:
            return None

        user = info.context.user

        if not user.is_authenticated:
            return None

        if user.is_admin:
            return obj

        if obj.sub == user.sub:
            return obj

        return None


class GroupNode(DjangoObjectType):
    class Meta:
        model = Group
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        """
        Only return node if user is an admin or is self
        """
        user = info.context.user
        if not user.has_perm("auth.view_group"):
            raise GraphQLError("Not allowed")

        try:
            obj = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Group not found")

        return obj


class PermissionNode(DjangoObjectType):
    class Meta:
        model = Permission
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        user = info.context.user
        if not user.has_perm("auth.view_permission"):
            raise GraphQLError("Not allowed")

        try:
            obj = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Permission not found")

        return obj
