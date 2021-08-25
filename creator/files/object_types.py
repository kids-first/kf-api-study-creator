from django.conf import settings
import graphene
from graphql import GraphQLError
from creator.data_templates.nodes.template_version import TemplateVersionNode


class TemplateMatchResult(graphene.ObjectType):
    """
    Encapsulates the results of evaluating whether a file Version matches
    a TemplateVersion

    A file matches a template when either the following
    two conditions are met:
        - If the template has required columns defined, then a match occurs
        when the file contains all of the required columns in the template
        - If the template has no required columns defined, then a match occurs
        when the file contains all of the optional columns in the template
    """
    matches_template = graphene.Boolean(
        description="Whether the file matches the template or not"
    )
    matched_required_cols = graphene.List(
        graphene.String,
        description="Intersection between file version columns and required "
        "template columns"
    )
    missing_required_cols = graphene.List(
        graphene.String,
        description="Difference between required template columns and file "
        "columns"
    )
    matched_optional_cols = graphene.List(
        graphene.String,
        description="Intersection between file version columns and optional "
        "template columns"
    )
    missing_optional_cols = graphene.List(
        graphene.String,
        description="Difference between optional template columns and "
        "file version columns"
    )
    template_version = graphene.Field(
        TemplateVersionNode,
        description="The template_version that the file version was evaluated "
        "against"
    )
