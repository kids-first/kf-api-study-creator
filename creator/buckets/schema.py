import re
import django_rq
from django.conf import settings
from graphene import relay, Mutation, Enum, Field, ID, InputObjectType, String
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, OrderingFilter
from graphql import GraphQLError
from graphql_relay import from_global_id

from .models import Bucket
from creator.studies.schema import StudyNode
from creator.studies.models import Study
from creator.events.models import Event


class BucketFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on"))

    class Meta:
        model = Bucket
        fields = ["name", "deleted", "study"]


class BucketNode(DjangoObjectType):
    class Meta:
        model = Bucket
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, name):
        """
        Only return bucket if user is admin
        """
        user = info.context.user
        if not user.has_perm("buckets.view_bucket"):
            raise GraphQLError("Not allowed")

        try:
            return cls._meta.model.objects.get(name=name)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("Bucket not found")

        return None


class LinkBucketMutation(Mutation):
    """
    Link a bucket to a study.
    If either do not exist, an error will be returned.
    If both are linked already, nothing will be done.
    May only be performed by an administrator
    """

    bucket = Field(BucketNode)
    study = Field(StudyNode)

    class Arguments:
        bucket = ID(
            required=True, description="The relay ID of the bucket to link"
        )
        study = ID(
            required=True,
            description="The relay ID of the study to link the bucket to",
        )

    def mutate(self, info, bucket, study):
        user = info.context.user

        if not user.has_perm("buckets.link_bucket"):
            raise GraphQLError("Not allowed")

        try:
            _, name = from_global_id(bucket)
            bucket = Bucket.objects.get(name=name)
        except (Bucket.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Bucket does not exist.")

        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Study does not exist.")

        bucket.study = study
        bucket.save()

        # Log an event
        message = (
            f"{user.username} linked bucket {bucket.name} to "
            f"study {study.kf_id}"
        )
        event = Event(
            study=study,
            bucket=bucket,
            description=message,
            event_type="BK_LIN",
        )
        # Only add the user if they are in the database (not a service user)
        if user and not user._state.adding:
            event.user = user
        event.save()

        return LinkBucketMutation(bucket=bucket, study=study)


class UnlinkBucketMutation(Mutation):
    """
    Unlink a bucket from a study.
    If either do not exist, an error will be returned.
    If they are not linked already, nothing will be done.
    May only be performed by an administrator.
    """

    bucket = Field(BucketNode)
    study = Field(StudyNode)

    class Arguments:
        bucket = ID(
            required=True, description="The relay ID of the bucketto link"
        )
        study = ID(
            required=True,
            description="The relay ID of the study to link the bucket to",
        )

    def mutate(self, info, bucket, study):
        user = info.context.user

        if not user.has_perm("buckets.unlink_bucket"):
            raise GraphQLError("Not allowed")

        try:
            _, name = from_global_id(bucket)
            bucket = Bucket.objects.get(name=name)
        except (Bucket.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Bucket does not exist.")

        try:
            _, study_id = from_global_id(study)
            study = Study.objects.get(kf_id=study_id)
        except (Study.DoesNotExist, UnicodeDecodeError):
            raise GraphQLError("Study does not exist.")

        bucket.study = None
        bucket.save()

        # Log an event
        message = (
            f"{user.username} unlinked bucket {bucket.name} from "
            f"study {study.kf_id}"
        )
        event = Event(
            study=study,
            bucket=bucket,
            description=message,
            event_type="BK_UNL",
        )

        # Only add the user if they are in the database (not a service user)
        if user and not user._state.adding:
            event.user = user
        event.save()
        return UnlinkBucketMutation(bucket=bucket, study=study)


class Query(object):
    bucket = relay.Node.Field(BucketNode, description="Get a single bucket")
    all_buckets = DjangoFilterConnectionField(
        BucketNode, filterset_class=BucketFilter, description="Get all buckets"
    )

    def resolve_all_buckets(self, info, **kwargs):
        """
        Return all buckets if the user has the 'list_all_bucket' permission
        """
        user = info.context.user
        if not user.has_perm("buckets.list_all_bucket"):
            raise GraphQLError("Not allowed")

        qs = Bucket.objects
        if kwargs.get("study") == "":
            qs = qs.filter(study=None)
        return qs.all()
