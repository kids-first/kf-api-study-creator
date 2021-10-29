from io import BytesIO
from django.http import HttpResponse, HttpResponseNotFound

from creator.data_templates.packaging import template_package
from creator.data_templates.models import TemplateVersion
from creator.events.models import Event
from creator.studies.models import Study

EXCEL_FORMAT = "excel"
ARCHIVE_FORMAT = "zip"
XLSX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
ZIP_MIME_TYPE = "application/zip"


def download_templates(request, study_kf_id=None):
    """
    If a study_kf_id is provided, download the study's data templates,
    optionally filtered by a list of ids. Otherwise, download template versions
    matching the provided list.

    Query parameters:
        file_format = [excel | zip]
        template_versions = comma separated str of ids

    Any authenticated user is allowed to download data templates
    """
    user = request.user

    if not user.is_authenticated:
        return HttpResponse("Not authorized to download templates", status=401)

    # Get template version ids
    tv_ids = request.GET.get("template_versions")
    if tv_ids:
        tv_ids = [tv.strip() for tv in tv_ids.split(",")]

    # When downloading a single template, the filename should be made using
    # the template name. Otherwise use the study ID if possible.
    if tv_ids and len(tv_ids) == 1:
        filename = f"{tv_ids[0]}_template"
    else:
        filename = (
            f"{study_kf_id}_templates" if study_kf_id else "template_package"
        )
    file_format = request.GET.get("file_format", EXCEL_FORMAT)
    if file_format == EXCEL_FORMAT:
        filename += ".xlsx"
        mime_type = XLSX_MIME_TYPE
    else:
        filename += ".zip"
        mime_type = ZIP_MIME_TYPE

    # Check if studies and template versions exist
    stream = BytesIO()
    try:
        stream, template_versions = template_package(
            study_kf_id=study_kf_id,
            filepath_or_buffer=stream,
            template_version_ids=tv_ids,
            excel_workbook=(file_format == EXCEL_FORMAT),
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

    # Fire a template download event for each template
    username = getattr(user, "display_name", "Anonymous user")
    tv_ids = ",".join(tv.pk for tv in template_versions)
    message = f"{username} downloaded template_versions: [{tv_ids}]"
    event = Event(
        user=user,
        organization=template_versions[0].data_template.organization,
        description=message,
        event_type="TV_DOW",
    )
    event.save()
    return response
