import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.analyses.analyzer import analyze_version
from creator.files.models import Version


class CreateAnalysisMutation(graphene.Mutation):
    class Arguments:
        version = graphene.ID(
            required=True, description="kf_id of the version to analyze"
        )

    analysis = graphene.Field("creator.analyses.schema.AnalysisNode")

    def mutate(self, info, version):
        """
        Run an analysis on a given version
        """
        user = info.context.user

        node_type, version_id = from_global_id(version)

        try:
            version = Version.objects.get(kf_id=version_id)
        except Version.DoesNotExist:
            raise GraphQLError("Version does not exist")

        study = version.root_file.study
        if not (
            user.has_perm("analyses.add_analysis")
            or (
                user.has_perm("analysis.add_my_study_analysis")
                and user.studies.filter(kf_id=study.kf_id).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        analysis = analyze_version(version)
        analysis.creator = user
        analysis.save()

        return CreateAnalysisMutation(analysis)


class Mutation:
    """ Mutations for analyses """

    create_analysis = CreateAnalysisMutation.Field(
        description="Create an analysis for a given document"
    )
