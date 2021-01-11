import urllib
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django.core.files.base import ContentFile
from django_s3_storage.storage import S3Storage
from botocore.exceptions import ClientError
from creator.files.models import File, Version, DevDownloadToken, DownloadToken
from creator.jobs.models import JobLog


def download_log(request, log_id):
    """
    """
    user = request.user

    # Check that the user is allowed to download the log
    if not (user.is_authenticated and (user.has_perm("jobs.view_joblog"))):
        return HttpResponse("Not authorized to view logs", status=401)

    try:
        log = JobLog.objects.get(id=log_id)
    except JobLog.DoesNotExist:
        return HttpResponseNotFound("No log exists with given ID")


    try:
        # Need to set storage location for study bucket if using S3 backend
        if settings.DEFAULT_FILE_STORAGE == "django_s3_storage.storage.S3Storage":
            log.log_file.storage = S3Storage(
                aws_s3_bucket_name=settings.LOG_BUCKET
            )

        response = HttpResponse(log.log_file)
        filename = log.log_file.name.split("/")[-1]
        response[
            "Content-Disposition"
        ] = f"attachment; filename*=UTF-8''{filename}"
        response["Content-Type"] = "application/octet-stream"
    except Exception as err:
        return HttpResponse(err, status=500)

    return response
