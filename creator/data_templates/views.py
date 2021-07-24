import urllib
import boto3
from io import BytesIO
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django_s3_storage.storage import S3Storage
from botocore.exceptions import ClientError

from creator.data_templates.packaging import study_template_package
from creator.data_templates.models import TemplateVersion
from creator.studies.models import Study

EXCEL_FORMAT = "excel"
ARCHIVE_FORMAT = "zip"
XLSX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
ZIP_MIME_TYPE = "application/zip"


def download_study_templates(request, study_kf_id):
    """
    Download the study's data templates

    Query parameters:
        file_format = [excel | zip]
        template_versions = comma separated str of ids

    If the template version IDs are provided in the query parameters, then
    filter the study's templates to only include those in the downloaded
    templates

    Any authenticated user is allowed to download a study's data templates
    """
    user = request.user

    if not user.is_authenticated:
        return HttpResponse(
            "Not authorized to download study templates", status=401
        )

    filename = f"{study_kf_id}_templates"
    file_format = request.GET.get("file_format", EXCEL_FORMAT)
    if file_format == EXCEL_FORMAT:
        filename += ".xlsx"
        mime_type = XLSX_MIME_TYPE
    else:
        filename += ".zip"
        mime_type = ZIP_MIME_TYPE

    # Get template version ids
    tv_ids = request.GET.get("template_versions")
    if tv_ids:
        tv_ids = [tv.strip() for tv in tv_ids.split(",")]

    # Check if studies and template versions exist
    stream = BytesIO()
    try:
        stream = study_template_package(
            study_kf_id,
            filepath_or_buffer=stream,
            template_version_ids=tv_ids,
            excel_workbook=(file_format == EXCEL_FORMAT)
        )
    except Study.DoesNotExist:
        return HttpResponseNotFound(
            f"Study with ID {study_kf_id} does not exist"
        )
    except TemplateVersion.DoesNotExist as e:
        # The study has no templates assigned OR
        # One or more template versions didn't exist
        return HttpResponseNotFound(str(e))
    except ValueError as e:
        # Input templates have duplicate names
        return HttpResponse(str(e), status=400)

    stream.seek(0)
    response = HttpResponse(stream.getvalue())
    response[
        "Content-Disposition"
    ] = f"attachment; filename*=UTF-8''{filename}"
    response["Content-Length"] = stream.getbuffer().nbytes
    response["Content-Type"] = mime_type
    stream.close()

    return response
