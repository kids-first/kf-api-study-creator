import urllib
from typing import Optional
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django_s3_storage.storage import S3Storage
from botocore.exceptions import ClientError

from .models import File, Version, DevDownloadToken, DownloadToken


def _resolve_version(
    file_id: str, version_id: Optional[str]
) -> (File, Version):
    """
    Returns a version either specified by the version_id, or the file's latest
    version if no version_id is specified
    """
    file = File.objects.get(kf_id=file_id)
    if version_id:
        obj = file.versions.get(kf_id=version_id)
    else:
        obj = file.versions.latest("created_at")
    return file, obj


def download(request, study_id, file_id, version_id=None):
    """
    Allow download if user is an admin OR user belongs to the file's study
    OR if there is an unclaimed token provided that has not expired.
    """
    user = request.user
    # Try to resolve a download token first from the url query params, then
    # from the Authorization header
    token = request.GET.get("token")
    if (
        not token
        and "HTTP_AUTHORIZATION" in request.META
        and request.META.get("HTTP_AUTHORIZATION").startswith("Token ")
    ):
        token = request.META.get("HTTP_AUTHORIZATION").replace("Token ", "")
    # If there is a token provided, check if it is valid for download
    download_token = None
    dev_token = None
    if token:
        # Try to resolve a signed url token
        try:
            download_token = DownloadToken.objects.get(token=token)
            _, obj = _resolve_version(file_id, version_id)
            if not download_token.is_valid(obj):
                download_token = None
        except (
            File.DoesNotExist,
            Version.DoesNotExist,
            DownloadToken.DoesNotExist,
        ):
            # If the file, version, or download token does not exist, just set
            # the token to None.
            # This could be inefficient as multiple trips may be made for the
            # same file/version information, but will not consider it for now
            download_token = None

        # Try to resolve a dev download token
        try:
            dev_token = DevDownloadToken.objects.get(token=token)
        except DevDownloadToken.DoesNotExist:
            dev_token = None

    try:
        file, obj = _resolve_version(file_id, version_id)
    except File.DoesNotExist:
        return HttpResponseNotFound("No file exists with given ID")
    except Version.DoesNotExist:
        return HttpResponseNotFound("No version exists with given ID")

    # Check that the user is allowed to download the file
    if not (
        user.is_authenticated
        and (  # User does not have permissions
            user.has_perm("files.view_version")
            or (
                user.has_perm("files.view_my_version")
                and user.studies.filter(
                    kf_id=obj.root_file.study.kf_id
                ).exists()
            )
        )
    ) and (  # There are no valid tokens
        download_token is None and dev_token is None
    ):
        return HttpResponse("Not authorized to download the file", status=401)

    # Don't return anything if the file does not belong to the requested study
    if file.study.kf_id != study_id:
        return HttpResponseNotFound('No file exists for given ID and study')

    # Need to set storage location for study bucket if using S3 backend
    if (settings.DEFAULT_FILE_STORAGE ==
            'django_s3_storage.storage.S3Storage'):
        obj.key.storage = S3Storage(aws_s3_bucket_name=file.study.bucket)

    # If we're using a token, mark it as claimed
    if download_token:
        download_token.claimed = True
        download_token.save()

    try:
        response = HttpResponse(obj.key)
    except (OSError, ClientError):
        # The file is no long at the path specified by the key
        return HttpResponseNotFound('Problem finding the file')

    file_name = urllib.parse.quote(obj.file_name)
    response[
        "Content-Disposition"
    ] = f"attachment; filename*=UTF-8''{obj.kf_id}_{file_name}"
    response['Content-Length'] = obj.size
    response['Content-Type'] = 'application/octet-stream'
    return response


def signed_url(request, study_id, file_id, version_id=None):
    """
    Generate a token for the requested version (defaults to the latest
    version). Authorization proceeds same as a download, but the return values
    is a url containing the generated token that will be intended to be passed
    back to the dowload endpoint.
    """
    user = request.user
    if not user.has_perm("files.add_downloadtoken"):
        return HttpResponseNotFound("Not authenticated to generate a url.")

    try:
        file = File.objects.get(kf_id=file_id)
    except File.DoesNotExist:
        return HttpResponseNotFound('No file exists with given ID')

    # Don't return anything if the file does not belong to the requested study
    if file.study.kf_id != study_id:
        return HttpResponseNotFound('No file exists for given ID and study')
    try:
        if version_id:
            obj = file.versions.get(kf_id=version_id)
        else:
            obj = file.versions.latest('created_at')
    except Version.DoesNotExist:
        return HttpResponseNotFound('No version exists with given ID')

    token = DownloadToken(root_version=obj)
    token.save()
    url = f'{obj.path}?token={token.token}'
    return JsonResponse({'url': url})
