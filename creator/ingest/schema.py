import django_filters
from graphql_relay import from_global_id
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError

from creator.ingest.models import Validation
from creator.ingest.mutations import Mutation


class ValidationNode(DjangoObjectType):
    class Meta:
        model = Validation
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        """
        Only return if the user is allowed to view validations
        """
        user = info.context.user

        if not (
            user.has_perm("ingest.view_validation")
            or user.has_perm("ingest.view_my_study_validation")
        ):
            raise GraphQLError("Not allowed")

        try:
            validation = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Validation does not exist")

        # NB: Because validations do not link to studies in anyway, we cannot
        # adequately check for non-admin privledges.
        if user.has_perm("ingest.view_validation") or (
            user.has_perm("ingest.view_my_study_validation")
            and user.studies.filter(kf_id=None).exists()
        ):
            return validation

        raise GraphQLError("Not allowed")


class ValidationFilter(django_filters.FilterSet):
    class Meta:
        model = Validation
        fields = ["creator"]

    order_by = django_filters.OrderingFilter(fields=("created_at",))


class Query(object):
    Validation = relay.Node.Field(
        ValidationNode, description="Get a single validation"
    )
    all_validations = DjangoFilterConnectionField(
        ValidationNode,
        filterset_class=ValidationFilter,
        description="Get all validations",
    )

    def resolve_all_validations(self, info, **kwargs):
        """
        Resolves all validations depending on the user's permissions
        """
        user = info.context.user

        if not (
            user.has_perm("ingest.list_all_validation")
            or user.has_perm("ingest.view_my_study_validation")
        ):
            raise GraphQLError("Not allowed")

        if user.has_perm("ingest.list_all_validation"):
            return Validation.objects.all()

        # NB: Need to update this if we ever tie validations to studies
        if user.has_perm("ingest.view_my_study_validation"):
            pass

        raise GraphQLError("Not allowed")
