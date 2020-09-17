import graphene
import django_rq
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.files.models import Version
from creator.ingest.models import Validation
from creator.ingest.tasks import run_validation


class CreateValidationMutation(graphene.Mutation):
    class Arguments:
        versions = graphene.List(
            graphene.ID,
            required=True,
            description="kf_id of the version to analyze",
        )

    validation = graphene.Field("creator.ingest.schema.ValidationNode")

    def mutate(self, info, versions):
        """
        Run a validation on a given set of input versions
        """
        user = info.context.user

        version_objects = []
        try:
            for version_id in versions:
                node_type, version_id = from_global_id(version_id)
                version = Version.objects.get(kf_id=version_id)
                version_objects.append(version)
        except Version.DoesNotExist:
            raise GraphQLError(f"Version {version_id} does not exist")

        # NB: Needs to be updated if validations are ever related to studies
        if not (
            user.has_perm("ingest.add_validation")
            or (
                user.has_perm("ingest.add_my_study_validation")
                and user.studies.filter(kf_id=None).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        validation = Validation(creator=info.context.user)
        validation.save()
        validation.versions.set(version_objects)
        validation_job = django_rq.enqueue(run_validation, validation.id)

        return CreateValidationMutation(validation)


class Mutation:
    """ Mutations for validations """

    create_validation = CreateValidationMutation.Field(
        description="Create a validation for a given set of versions"
    )
