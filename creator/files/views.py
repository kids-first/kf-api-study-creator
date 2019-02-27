from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.conf import settings
from django_s3_storage.storage import S3Storage
from .models import File


# Create your views here.
def download(request, study_id, file_id):
    try:
        file = File.objects.get(id=file_id)
    except File.DoesNotExist:
        return HttpResponseNotFound('No file exists with given ID')
    obj = file.versions.latest('created_at')
    # Need to set storage location for study bucket if using S3 backend
    if (settings.DEFAULT_FILE_STORAGE ==
            'django_s3_storage.storage.S3Storage'):
        obj.key.storage = S3Storage(aws_s3_bucket_name=file.study.bucket)

    response = HttpResponse(obj.key)
    response['Content-Disposition'] = f'attachment; filename={file.name}'
    response['Content-Length'] = obj.size
    return response
