import urllib
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django_s3_storage.storage import S3Storage
from botocore.exceptions import ClientError

from .models import File, Object, DownloadToken


def download(request,  study_id, file_id, version_id=None):
    """
    Only allow downloading if user is an admin or is in the study group
    """
    user = request.user
    if (user is None or not user.is_authenticated or
       study_id not in user.ego_groups and 'ADMIN' not in user.ego_roles):
        return HttpResponseNotFound('Not authenticated to download the file.')

    try:
        file = File.objects.get(kf_id=file_id)
    except File.DoesNotExist:
        return HttpResponseNotFound('No file exists with given ID')
    try:
        if version_id:
            obj = file.versions.get(kf_id=version_id)
        else:
            obj = file.versions.latest('created_at')
    except Object.DoesNotExist:
        return HttpResponseNotFound('No version exists with given ID')

    # Need to set storage location for study bucket if using S3 backend
    if (settings.DEFAULT_FILE_STORAGE ==
            'django_s3_storage.storage.S3Storage'):
        obj.key.storage = S3Storage(aws_s3_bucket_name=file.study.bucket)

    try:
        response = HttpResponse(obj.key)
    except (OSError, ClientError):
        # The file is no long at the path specified by the key
        return HttpResponseNotFound('Problem finding the file')

    file_name = urllib.parse.quote(file.name)
    response['Content-Disposition'] = f'attachment; filename={file_name}'
    response['Content-Length'] = obj.size
    return response


def signed_url(request, study_id, file_id, version_id=None):
    """
    Generate a token for the requested object (defaults to the latest version).
    Authorization proceeds same as a download, but the return values is a
    url containing the generated token that will be intended to be passed
    back to the dowload endpoint.
    """
    user = request.user
    if (user is None or not user.is_authenticated or
       study_id not in user.ego_groups and 'ADMIN' not in user.ego_roles):
        return HttpResponseNotFound('Not authenticated to generate a url.')

    try:
        file = File.objects.get(kf_id=file_id)
    except File.DoesNotExist:
        return HttpResponseNotFound('No file exists with given ID')
    try:
        if version_id:
            obj = file.versions.get(kf_id=version_id)
        else:
            obj = file.versions.latest('created_at')
    except Object.DoesNotExist:
        return HttpResponseNotFound('No version exists with given ID')

    token = DownloadToken(root_object=obj)
    token.save()
    url = f'{obj.path}?token={token.token}'
    return JsonResponse({'url': url})
