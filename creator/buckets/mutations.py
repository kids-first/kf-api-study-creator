import graphene
from graphql import GraphQLError
from graphql_relay import from_global_id

from creator.buckets.models import Bucket
from creator.events.models import Event
from creator.studies.models import Study


class LinkBucketMutation(graphene.Mutation):
    """
    Link a bucket to a study.
    If either do not exist, an error will be returned.
    If both are linked already, nothing will be done.
    May only be performed by an administrator
    """

    bucket = graphene.Field("creator.buckets.schema.BucketNode")
    study = graphene.Field("creator.studies.schema.StudyNode")

    class Arguments:
        bucket = graphene.ID(
            required=True, description="The relay ID of the bucket to link"
        )
        study = graphene.ID(
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
            f"{user.display_name} linked bucket {bucket.name} to "
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


class UnlinkBucketMutation(graphene.Mutation):
    """
    Unlink a bucket from a study.
    If either do not exist, an error will be returned.
    If they are not linked already, nothing will be done.
    May only be performed by an administrator.
    """

    bucket = graphene.Field("creator.buckets.schema.BucketNode")
    study = graphene.Field("creator.studies.schema.StudyNode")

    class Arguments:
        bucket = graphene.ID(
            required=True, description="The relay ID of the bucketto link"
        )
        study = graphene.ID(
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
            f"{user.display_name} unlinked bucket {bucket.name} from "
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


class Mutation(graphene.ObjectType):
    link_bucket = LinkBucketMutation.Field(
        description="Link a bucket to a Study"
    )
    unlink_bucket = UnlinkBucketMutation.Field(
        description="Unlink a bucket from a Study"
    )
