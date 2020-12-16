from django_rq.utils import get_statistics
from django.conf import settings
from django.core.cache import cache
import graphene
from graphql import GraphQLError
from creator.status.settings.nodes import Features, Settings


def get_version_info():
    from creator.version_info import COMMIT, VERSION

    return {"commit": COMMIT, "version": VERSION}


class Status(graphene.ObjectType):
    name = graphene.String()
    version = graphene.String()
    commit = graphene.String()
    features = graphene.Field(Features)
    settings = graphene.Field(Settings)
    queues = graphene.JSONString()

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
            "create_slack_channels": settings.FEAT_SLACK_CREATE_CHANNELS,
            "slack_send_release_notifications": (
                settings.FEAT_SLACK_SEND_RELEASE_NOTIFICATIONS
            ),
        }

        return Features(**features)

    def resolve_settings(self, info):
        """
        Settings may only be resolved by an admin
        """
        user = info.context.user
        if not user.has_perm("jobs.view_settings"):
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
            "slack_users": settings.SLACK_USERS,
            "log_dir": settings.LOG_DIR,
            "log_bucket": settings.LOG_BUCKET,
        }
        return Settings(**conf)

    def resolve_queues(self, info):
        """
        Queues may only be resolved by an admin
        """
        user = info.context.user
        if not user.has_perm("jobs.view_queue"):
            raise GraphQLError("Not allowed")

        stats = get_statistics().get("queues")

        # Remove connection info
        cleaned = []
        for stat in stats:
            if "connection_kwargs" in stat:
                del stat["connection_kwargs"]
            cleaned.append(stat)

        return cleaned


class Query(graphene.ObjectType):

    status = graphene.Field(Status)

    def resolve_status(parent, info):
        """
        Return status information about the study creator.
        """
        # Retrieve from cache in the case that we have to parse git commands
        # to get version details.
        info = cache.get_or_set("VERSION_INFO", get_version_info)

        return Status(name="Kids First Study Creator", **info)
