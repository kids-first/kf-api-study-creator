from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView
import creator.files.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        r'',
        csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))
    ),
    path(
        r'graphql',
        csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))
    ),
    path(
        r'download/study/<study_id>/file/<file_id>/version/<version_id>',
        creator.files.views.download
    ),
    path(
        r'download/study/<study_id>/file/<file_id>',
        creator.files.views.download_latest
    )
]
