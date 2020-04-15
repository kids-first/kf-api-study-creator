from django.urls import path, include
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from graphene_file_upload.django import FileUploadGraphQLView
import creator.files.views


def health_check(request):
    return HttpResponse('ok')


urlpatterns = [
    path('health_check', health_check),
    path(
        r'',
        csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))
    ),
    path(
        r'graphql',
        csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))
    ),
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
    )
]

if settings.DEVELOPMENT_ENDPOINTS:
    import creator.dev.views

    urlpatterns.append(path(r"__dev/", include("creator.dev.urls")))
