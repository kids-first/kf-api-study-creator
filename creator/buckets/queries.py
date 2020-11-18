from datetime import datetime
import graphene
from collections import defaultdict, Counter
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


class Stat(graphene.ObjectType):
    metric = graphene.String()
    value = graphene.Float()


class BucketInventoryStats(graphene.ObjectType):
    total_objects = graphene.Float()
    total_bytes = graphene.Float()
    total_buckets = graphene.Float()
    count_by_is_latest = graphene.List(Stat)
    count_by_storage_class = graphene.List(Stat)
    count_by_replication_status = graphene.List(Stat)
    count_by_encryption_status = graphene.List(Stat)
    size_by_is_latest = graphene.List(Stat)
    size_by_storage_class = graphene.List(Stat)
    size_by_replication_status = graphene.List(Stat)
    size_by_encryption_status = graphene.List(Stat)


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

        count_aggs = defaultdict(lambda: defaultdict(int))
        size_aggs = defaultdict(lambda: defaultdict(int))

        def combine(c, group, metric):
            return Counter(c) + Counter(
                inventory.summary.get(group, {}).get(metric, {})
            )

        def to_list(agg):
            return [{"metric": k, "value": v} for k, v in agg.items()]

        for inventory in latest_inventories:
            total_count += inventory.summary.get("total_count", 0)
            total_bytes += inventory.summary.get("total_size", 0)

            for metric in [
                "is_latest",
                "storage_class",
                "replication_status",
                "encryption_status",
            ]:
                count_aggs[metric] = combine(
                    count_aggs[metric], "count", metric
                )
                size_aggs[metric] = combine(size_aggs[metric], "size", metric)

        return BucketInventoryStats(
            total_objects=total_count,
            total_bytes=total_bytes,
            total_buckets=total_buckets,
            count_by_is_latest=to_list(count_aggs["is_latest"]),
            count_by_storage_class=to_list(count_aggs["storage_class"]),
            count_by_replication_status=to_list(
                count_aggs["replication_status"]
            ),
            count_by_encryption_status=to_list(
                count_aggs["encryption_status"]
            ),
            size_by_is_latest=to_list(size_aggs["is_latest"]),
            size_by_storage_class=to_list(size_aggs["storage_class"]),
            size_by_replication_status=to_list(
                size_aggs["replication_status"]
            ),
            size_by_encryption_status=to_list(size_aggs["encryption_status"]),
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
