from graphene.types import Scalar
from graphql.language import ast
from graphene.types.scalars import MIN_INT, MAX_INT
from graphene import relay, Field, Enum
from graphql import GraphQLError
from graphene_django import DjangoObjectType

from creator.storage_analyses.models import (
    StorageAnalysis,
    FileAudit,
    ResultEnum
)


def description(e):
    if e is None:
        return
    return e.value


AuditResultEnum = Enum.from_enum(ResultEnum, description=description)


class BigInt(Scalar):
    """
    BigInt is an extension of the regular Int field
    that supports Integers bigger than a signed
    32-bit integer.
    """
    @staticmethod
    def big_to_float(value):
        num = int(value)
        if num > MAX_INT or num < MIN_INT:
            return float(int(num))
        return num

    serialize = big_to_float
    parse_value = big_to_float

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.IntValue):
            num = int(node.value)
            if num > MAX_INT or num < MIN_INT:
                return float(int(num))
            return num


class StorageAnalysisNode(DjangoObjectType):

    class Meta:
        model = StorageAnalysis
        interfaces = (relay.Node,)
        filter_fields = ()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        try:
            storage_analysis = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("StorageAnalysis does not exist")

        if not (
            user.has_perm("storage_analyses.view_storageanalysis")
            and user.studies.filter(
                kf_id=storage_analysis.study.kf_id
            ).exists()
        ):
            raise GraphQLError("Not allowed")

        return storage_analysis


class FileAuditNode(DjangoObjectType):
    expected_size = Field(BigInt)
    actual_size = Field(BigInt)

    class Meta:
        model = FileAudit
        interfaces = (relay.Node,)
        filter_fields = ()

    result = AuditResultEnum()

    @classmethod
    def get_node(cls, info, id):
        """
        Check permissions and return
        """
        user = info.context.user

        try:
            file_audit = cls._meta.model.objects.get(pk=id)
        except cls._meta.model.DoesNotExist:
            raise GraphQLError("FileAudit does not exist")

        if not (
            user.has_perm("storage_analyses.view_storageanalysis")
            and user.studies.filter(
                kf_id__in=file_audit.study.kf_id
            ).exists()
        ):
            raise GraphQLError("Not allowed")

        return file_audit
