import graphene
from django.conf import settings
import django_rq
from django_rq.utils import get_statistics
from django.core.cache import cache
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter

from creator.models import Job

from creator.buckets.schema import Mutation as BucketMutation
from creator.files.schema import (
    FileMutation,
    VersionMutation,
    DownloadMutation,
)
from creator.projects.schema import Mutation as ProjectMutation
from creator.studies.schema import Mutation as StudyMutation
from creator.users.schema import Mutation as UserMutation
import creator.events.schema
from creator.referral_tokens import schema as referral_tokens_mutations


def get_version_info():
    from creator.version_info import COMMIT, VERSION

    return {"commit": COMMIT, "version": VERSION}


class Features(graphene.ObjectType):
    study_creation = graphene.Boolean(
        description=(
            "Will create new studies in the dataservice when a createStudy "
            "mutation is performed"
        )
    )
    study_updates = graphene.Boolean(
        description=(
            "Studies will be updated in the dataservice when "
            "changed through an updateStudy mutation"
        )
    )
    cavatica_create_projects = graphene.Boolean(
        description=(
            "Cavatica projects may be created through the createProject "
            "mutation"
        )
    )
    cavatica_copy_users = graphene.Boolean(
        description=(
            "Users will be copied from the CAVATICA_USER_ACCESS_PROJECT to "
            "any new project"
        )
    )
    cavatica_mount_volumes = graphene.Boolean(
        description=(
            "New projects will automatically have a new S3 volume mounted"
        )
    )
    study_buckets_create_buckets = graphene.Boolean(
        description=(
            "New buckets will be created for new studies when a new study is "
            "created"
        )
    )
    create_slack_channels = graphene.Boolean(
        description=("Create a Slack channel for new studies")
    )


class Settings(graphene.ObjectType):
    development_endpoints = graphene.Boolean(
        description=("Developer endpoints are active")
    )
    dataservice_url = graphene.String(description="The URL of the Dataservice")
    cavatica_url = graphene.String(description="The URL of the Cavatica API")
    cavatica_delivery_account = graphene.String(
        description="The Cavatica account used for delivery projects"
    )
    cavatica_harmonization_account = graphene.String(
        description=(
            "The Cavatica account used for harmonization and " "other projects"
        )
    )
    cavatica_user_access_project = graphene.String(
        description="The project to copy users from for new projects"
    )
    study_buckets_region = graphene.String(
        description=("The AWS region where new study buckets will be created")
    )
    study_buckets_logging_bucket = graphene.String(
        description=(
            "The bucket where access logs for the new study buckets will be "
            "stored"
        )
    )
    study_buckets_dr_region = graphene.String(
        description=(
            "The AWS region where new study buckets recovery buckets "
            "will be created"
        )
    )
    study_buckets_dr_logging_bucket = graphene.String(
        description=(
            "The bucket where access logs for the new study bucket recovery "
            "buckets will be stored"
        )
    )
    study_buckets_inventory_location = graphene.String(
        description=(
            "The full aws bucket with prefix where bucket inventories will be "
            "dumped"
        )
    )
    study_buckets_log_prefix = graphene.String(
        description=(
            "The prefix under which access logs will be stored in the logging "
            "and dr logging buckets"
        )
    )
    slack_users = graphene.List(
        graphene.String,
        description=("Slack IDs of users to add to new study channels"),
    )


class JobNode(DjangoObjectType):
    enqueued_at = graphene.DateTime()

    class Meta:
        model = Job
        interfaces = (graphene.relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, name):
        """
        Only return node if user is admin
        """
        user = info.context.user

        if not user.has_perm("creator.view_job"):
            return Job.objects.none()

        return Job.objects.get(name=name)


class JobFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on", "last_run"))

    class Meta:
        model = Job
        fields = ["name", "active", "failing"]


class Status(graphene.ObjectType):
    name = graphene.String()
    version = graphene.String()
    commit = graphene.String()
    features = graphene.Field(Features)
    settings = graphene.Field(Settings)
    queues = graphene.JSONString()
    jobs = DjangoFilterConnectionField(
        JobNode, filterset_class=JobFilter, description="Get job statuses"
    )

    def resolve_features(self, info):
        features = {
            "study_creation": settings.FEAT_DATASERVICE_CREATE_STUDIES,
            "study_updates": settings.FEAT_DATASERVICE_UPDATE_STUDIES,
            "cavatica_create_projects": settings.FEAT_CAVATICA_CREATE_PROJECTS,
            "cavatica_copy_users": settings.FEAT_CAVATICA_COPY_USERS,
            "cavatica_mount_volumes": settings.FEAT_CAVATICA_MOUNT_VOLUMES,
            "study_buckets_create_buckets": (
                settings.FEAT_STUDY_BUCKETS_CREATE_BUCKETS
            ),
            "create_slack_channels": (settings.FEAT_SLACK_CREATE_CHANNELS),
        }

        return Features(**features)

    def resolve_settings(self, info):
        """
        Settings may only be resolved by an admin
        """
        user = info.context.user
        if not user.has_perm("creator.view_settings"):
            raise GraphQLError("Not allowed")

        conf = {
            "development_endpoints": settings.DEVELOPMENT_ENDPOINTS,
            "dataservice_url": settings.DATASERVICE_URL,
            "cavatica_url": settings.CAVATICA_URL,
            "cavatica_delivery_account": settings.CAVATICA_DELIVERY_ACCOUNT,
            "cavatica_harmonization_account": (
                settings.CAVATICA_HARMONIZATION_ACCOUNT
            ),
            "cavatica_user_access_project": (
                settings.CAVATICA_USER_ACCESS_PROJECT
            ),
            "study_buckets_region": settings.STUDY_BUCKETS_REGION,
            "study_buckets_logging_bucket": (
                settings.STUDY_BUCKETS_LOGGING_BUCKET
            ),
            "study_buckets_dr_region": settings.STUDY_BUCKETS_DR_REGION,
            "study_buckets_dr_logging_bucket": (
                settings.STUDY_BUCKETS_DR_LOGGING_BUCKET
            ),
            "study_buckets_inventory_location": (
                settings.STUDY_BUCKETS_INVENTORY_LOCATION
            ),
            "study_buckets_log_prefix": settings.STUDY_BUCKETS_LOG_PREFIX,
            "slack_users": (settings.SLACK_USERS),
        }
        return Settings(**conf)

    def resolve_queues(self, info):
        """
        Queues may only be resolved by an admin
        """
        user = info.context.user
        if not user.has_perm("creator.view_queue"):
            raise GraphQLError("Not allowed")

        stats = get_statistics().get("queues")

        # Remove connection info
        cleaned = []
        for stat in stats:
            if "connection_kwargs" in stat:
                del stat["connection_kwargs"]
            cleaned.append(stat)

        return cleaned

    def resolve_jobs(self, info):
        """
        Jobs may only be resolved by an admin
        """
        user = info.context.user
        if not user.has_perm("creator.view_job"):
            raise GraphQLError("Not allowed")

        return Job.objects.all()


class Query(
    creator.files.schema.FileQuery,
    creator.files.schema.VersionQuery,
    creator.files.schema.DownloadQuery,
    creator.studies.schema.Query,
    creator.users.schema.Query,
    creator.events.schema.Query,
    creator.projects.schema.Query,
    creator.buckets.schema.Query,
    referral_tokens_mutations.Query,
    graphene.ObjectType,
):
    status = graphene.Field(Status)

    def resolve_status(parent, info):
        """
        Return status information about the study creator.
        """
        # Retrieve from cache in the case that we have to parse git commands
        # to get version details.
        info = cache.get_or_set("VERSION_INFO", get_version_info)

        return Status(name="Kids First Study Creator", **info)


class Mutation(
    BucketMutation,
    ProjectMutation,
    StudyMutation,
    FileMutation,
    VersionMutation,
    DownloadMutation,
    UserMutation,
    graphene.ObjectType,
):
    create_referral_token = (
        referral_tokens_mutations.CreateReferralTokenMutation.Field(
            description="Create a referral token"
        )
    )
    exchange_referral_token = (
        referral_tokens_mutations.ExchangeReferralTokenMutation.Field(
            description="Exchange a referral token"
        )
    )


schema = graphene.Schema(query=Query, mutation=Mutation)
