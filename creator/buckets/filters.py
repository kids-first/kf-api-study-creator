from django_filters import FilterSet, OrderingFilter

from creator.buckets.models import Bucket, BucketInventory


class BucketFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on"))

    class Meta:
        model = Bucket
        fields = ["name", "deleted", "study"]


class BucketInventoryFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))

    class Meta:
        model = BucketInventory
        fields = ["bucket__name"]
