from django.conf import settings
import graphene
from graphene import relay
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.ingest_runs.models import ValidationResultset


class ValidationResultsetNode(DjangoObjectType):
    class Meta:
        model = ValidationResultset
        interfaces = (relay.Node,)

    download_report_url = graphene.String()
    download_results_url = graphene.String()

    def resolve_download_report_url(self, info):
        protocol = "http" if settings.DEVELOP else "https"
        return f"{protocol}://{info.context.get_host()}{self.report_path}"

    def resolve_download_results_url(self, info):
        protocol = "http" if settings.DEVELOP else "https"
        return f"{protocol}://{info.context.get_host()}{self.results_path}"

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        try:
            validation_rs = cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("ValidationResultsets was not found")

        if not (
            user.has_perm("data_reviews.view_datareview")
            or (
                user.has_perm("data_reviews.view_my_study_datareview")
                and user.studies.filter(
                    kf_id=validation_rs.study.kf_id
                ).exists()
            )
        ):
            raise GraphQLError("Not allowed")

        return validation_rs
