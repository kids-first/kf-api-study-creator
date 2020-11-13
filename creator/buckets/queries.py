from datetime import datetime
import graphene
from collections import defaultdict
from graphene import relay
from graphql import GraphQLError
from django.db.models import Sum
from django.db.models.functions import TruncDate
from graphene_django.filter import DjangoFilterConnectionField

from creator.buckets.nodes import BucketNode, BucketInventoryNode
from creator.buckets.models import Bucket, BucketInventory
from creator.buckets.filters import BucketFilter, BucketInventoryFilter


class DataPointType(graphene.ObjectType):
    size = graphene.Float()
    date = graphene.DateTime()


class FileFormatStat(graphene.ObjectType):
    file_format = graphene.String()
    value = graphene.Float()


class BucketInventoryStats(graphene.ObjectType):
    total_objects = graphene.Float()
    total_bytes = graphene.Float()
    total_buckets = graphene.Float()
    count_by_file_format = graphene.List(FileFormatStat)
    size_by_file_format = graphene.List(FileFormatStat)


class Query:
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

        qs = Bucket.objects.filter(deleted=False)
        if kwargs.get("study") == "":
            qs = qs.filter(study=None)
        return qs.all()

    bucket_inventory = relay.Node.Field(
        BucketInventoryNode, description="Get a single bucket inventory"
    )
    all_bucket_inventories = DjangoFilterConnectionField(
        BucketInventoryNode,
        filterset_class=BucketInventoryFilter,
        description="Get all bucket inventories",
    )

    def resolve_all_bucket_inventories(self, info, **kwargs):
        """
        Return all bucket inventories
        """
        user = info.context.user

        if not user.has_perm("bucket_inventories.list_all_bucketinventory"):
            raise GraphQLError("Not allowed")

        return BucketInventory.objects.all()

    bucket_inventory_stats = graphene.Field(
        BucketInventoryStats, group_by=graphene.String(required=False)
    )

    def resolve_bucket_inventory_stats(self, info):
        latest_inventories = BucketInventory.objects.order_by(
            "bucket_id", "-creation_date"
        ).distinct("bucket_id")

        total_buckets = Bucket.objects.filter(deleted=False).count()
        total_count = 0
        total_bytes = 0
        count_by_file_format = defaultdict(int)
        size_by_file_format = defaultdict(int)
        for inventory in latest_inventories:
            total_count += inventory.summary.get("total_count", 0)
            total_bytes += inventory.summary.get("total_size", 0)
            continue

            # Aggregate by file format
            for k, v in (
                inventory.summary.get("count").get("by_file_format").items()
            ):
                count_by_file_format[k] += v
            for k, v in (
                inventory.summary.get("size").get("by_file_format").items()
            ):
                size_by_file_format[k] += v

        # Convert counts and size aggregations into lists of dicts
        count_by_file_format = [
            {"file_format": k, "value": v}
            for k, v in count_by_file_format.items()
        ]
        size_by_file_format = [
            {"file_format": k, "value": v}
            for k, v in size_by_file_format.items()
        ]

        return BucketInventoryStats(
            total_objects=total_count,
            total_bytes=total_bytes,
            total_buckets=total_buckets,
            count_by_file_format=count_by_file_format,
            size_by_file_format=size_by_file_format,
        )

    bucket_size = graphene.List(DataPointType)

    def resolve_bucket_size(self, info, group_by=None, **kwargs):
        data = (
            BucketInventory.objects.filter(bucket__deleted=False)
            .filter(summary__summary_version=1)
            .values("bucket__name", "creation_date", "summary__total_size")
            .order_by("creation_date")
            .all()
        )

        curr_values = {k: 0 for k in set(b["bucket__name"] for b in data)}
        dates = defaultdict(datetime)
        for point in data:
            date = point["creation_date"]
            if point["summary__total_size"] is None:
                continue
            curr_values[point["bucket__name"]] = point["summary__total_size"]
            dates[datetime.combine(date, datetime.min.time())] = sum(
                curr_values.values()
            )

        line = [{"date": k, "size": v} for k, v in dates.items()]
        return sorted(line, key=lambda x: x["date"])
