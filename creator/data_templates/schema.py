import graphene

from creator.data_templates.queries.data_template import (
    Query as DataTemplateQuery,
)
from creator.data_templates.mutations.data_template import (
    Mutation as DataTemplateMutation,
)
from creator.data_templates.queries.template_version import (
    Query as TemplateVersionQuery,
)
from creator.data_templates.mutations.template_version import (
    Mutation as TemplateVersionMutation,
)
from creator.data_templates.mutations.study_templates import (
    Mutation as StudyTemplateMutation,
)


class Query(DataTemplateQuery, TemplateVersionQuery, graphene.ObjectType):
    pass


class Mutation(
    DataTemplateMutation,
    TemplateVersionMutation,
    StudyTemplateMutation,
    graphene.ObjectType,
):
    pass
