from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.ingest_runs.models import ValidationRun


class ValidationRunNode(DjangoObjectType):
    class Meta:
        model = ValidationRun
        interfaces = (relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        try:
            validation_run = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("ValidationRuns was not found")

        if not (
            user.has_perm("ingest_runs.view_validationrun")
            or (
                user.has_perm("ingest_runs.view_my_study_validationrun")
                and user.studies.filter(
                    kf_id=validation_run.study.kf_id
                ).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        return validation_run
