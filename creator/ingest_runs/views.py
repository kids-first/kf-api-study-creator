import urllib
import boto3
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django_s3_storage.storage import S3Storage
from botocore.exceptions import ClientError
from creator.data_reviews.models import DataReview
from creator.ingest_runs.models import ValidationResultset

# Maps endpont to correct DataReview FileField
FILE_FIELD_MAP = {"report": "report_file", "results": "results_file"}
S3_STORAGE = "django_s3_storage.storage.S3Storage"


def download_validation_file(request, review_id, file_type):
    """
    Download the data review's validation report or results file

    Allow download if user is admin or user belongs to the data review's
    study
    """
    user = request.user

    try:
        review = DataReview.objects.get(kf_id=review_id)
    except DataReview.DoesNotExist:
        return HttpResponseNotFound("No data review exists with given ID")

    # Check that the user is allowed to download the validation file
    if not (
        user.is_authenticated
        and
        # Must have general view or view for my study permissions
        (
            user.has_perm("data_reviews.view_datareview")
            or (
                user.has_perm("data_reviews.view_my_study_datareview")
                and user.studies.filter(kf_id=review.study.kf_id).exists()
            )
        )
    ):
        return HttpResponse("Not authorized to view data review", status=401)

    # Set bucket to study bucket if storage backend is S3
    try:
        file_field = getattr(
            review.validation_resultset, FILE_FIELD_MAP.get(file_type)
        )
    except ValidationResultset.DoesNotExist:
        # Data review does not have a validation result set yet
        return HttpResponseNotFound(
            "Validation results not yet available for this data review"
        )
    if settings.DEFAULT_FILE_STORAGE == S3_STORAGE:
        file_field.storage = S3Storage(aws_s3_bucket_name=review.study.bucket)

    # Check if file exists in storage system
    if not (file_field and file_field.storage.exists(file_field.name)):
        return HttpResponseNotFound("Validation file does not exist")

    response = HttpResponse(file_field)
    filename = file_field.name.split("/")[-1]
    response[
        "Content-Disposition"
    ] = f"attachment; filename*=UTF-8''{filename}"
    response["Content-Length"] = file_field.storage.size(file_field.name)
    response["Content-Type"] = "application/octet-stream"

    return response
