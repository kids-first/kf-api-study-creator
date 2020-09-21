import django_filters
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter
from graphql import GraphQLError

from creator.jobs.models import JobLog


class JobLogFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_at",))

    class Meta:
        model = JobLog
        # fields = {"job": ["exact"]}
        fields = []


class JobLogNode(DjangoObjectType):
    class Meta:
        model = JobLog
        interfaces = (relay.Node,)
        filter_fields = ()
        exclude = ("log_file",)

    download_url = graphene.String()

    def resolve_download_url(self, info):
        return f"http://{info.context.get_host()}{self.path}"

    @classmethod
    def get_node(cls, info, id):
        """
        """
        user = info.context.user
        if not user.has_perm("jobs.view_joblog"):
            raise GraphQLError("Not allowed")

        try:
            return cls._meta.model.objects.get(id=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Job Log not found")

        return None


class Query(object):
    job_log = relay.Node.Field(JobLogNode, description="Get a single job log")
    all_job_logs = DjangoFilterConnectionField(
        JobLogNode,
        filterset_class=JobLogFilter,
        description="Get all job logs",
    )

    def resolve_all_job_logs(self, info, **kwargs):
        """
        """
        user = info.context.user
        if not user.has_perm("jobs.list_all_joblog"):
            raise GraphQLError("Not allowed")

        return JobLog.objects.all()
