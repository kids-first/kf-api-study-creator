from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django_filters import FilterSet, OrderingFilter, CharFilter

from creator.data_reviews.nodes import DataReviewNode
from creator.data_reviews.models import DataReview


class DataReviewFilter(FilterSet):
    order_by = OrderingFilter(fields=("created_on",))
    study_kf_id = CharFilter(field_name="study__kf_id", lookup_expr="exact")

    class Meta:
        model = DataReview
        fields = []


class Query(object):
    data_review = relay.Node.Field(
        DataReviewNode, description="Get a single data_review"
    )
    all_data_reviews = DjangoFilterConnectionField(
        DataReviewNode,
        filterset_class=DataReviewFilter,
        description="Get all data_reviews",
    )

    def resolve_all_data_reviews(self, info, **kwargs):
        """
        Return all data_reviews
        """
        user = info.context.user

        if not user.has_perm("data_reviews.list_all_datareview"):
            raise GraphQLError("Not allowed")

        return DataReview.objects.all()
