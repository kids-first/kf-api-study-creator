from django.urls import path, include
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from creator.views import SentryGraphQLView
import creator.files.views
import creator.extract_configs.views
import creator.jobs.views
import creator.ingest_runs.views
import creator.data_templates.views


def health_check(request):
    return HttpResponse("ok")


class GraphQLView(SentryGraphQLView):
    """
    Custom view that overwrites error formatting to handle Django form
    validation errors more natively.
    """

    @staticmethod
    def format_error(error):
        formatted_error = super(
            SentryGraphQLView, SentryGraphQLView
        ).format_error(error)

        if (
            hasattr(error, "original_error")
            and isinstance(error.original_error, ValidationError)
            and hasattr(error.original_error, "error_dict")
        ):
            error_dict = error.original_error.error_dict
            if "__all__" in error_dict:
                formatted_error["message"] = ", ".join(
                    [e.message for e in error_dict["__all__"]]
                )

        return formatted_error


urlpatterns = [
    path("health_check", health_check),
    path(r"", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path(r"graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path("django-rq/", include("django_rq.urls")),
    path(
        r'download/study/<study_id>/file/<file_id>/version/<version_id>',
        creator.files.views.download
    ),
    path(
        r'download/study/<study_id>/file/<file_id>',
        creator.files.views.download
    ),
    path(
        r'signed-url/study/<study_id>/file/<file_id>/version/<version_id>',
        creator.files.views.signed_url
    ),
    path(
        r'signed-url/study/<study_id>/file/<file_id>',
        creator.files.views.signed_url
    ),
    path(
        r'extract_config/study/<study_id>/file/<file_id>/version/<version_id>',
        creator.extract_configs.views.download_config,
    ),
    path(
        r'extract_config/study/<study_id>/file/<file_id>',
        creator.extract_configs.views.download_config,
    ),
    path(r"logs/<log_id>", creator.jobs.views.download_log),
    path(
        r'download/data_review/<review_id>/validation/<file_type>',
        creator.ingest_runs.views.download_validation_file
    ),
    path(
        r'download/templates/<study_kf_id>',
        creator.data_templates.views.download_templates
    ),
    path(
        r'download/templates',
        creator.data_templates.views.download_templates
    ),
]

if settings.DEVELOPMENT_ENDPOINTS:
    import creator.dev.views

    urlpatterns.append(path(r"__dev/", include("creator.dev.urls")))
