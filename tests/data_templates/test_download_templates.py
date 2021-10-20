from io import BytesIO
import pytest
import pandas

from creator.studies.factories import StudyFactory, Study
from creator.events.models import Event
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory,
    TemplateVersion,
)
from creator.data_templates.views import ZIP_MIME_TYPE, XLSX_MIME_TYPE


@pytest.fixture
def template_versions(db):
    """
    Create different data templates with one version each. Assign templates
    to a study within an organization
    """
    study = StudyFactory()
    dts = DataTemplateFactory.create_batch(2, organization=study.organization)
    return [
        TemplateVersionFactory(data_template=dt, studies=[study]) for dt in dts
    ]


@pytest.fixture
def template_versions_mult_studies(db):
    tvs = []
    studies = StudyFactory.create_batch(4)
    for study in studies:
        dt = DataTemplateFactory(organization=study.organization)
        tvs.append(TemplateVersionFactory(data_template=dt, studies=[study]))
    return tvs


@pytest.mark.parametrize(
    "exc,status_code",
    [
        (Study.DoesNotExist, 404),
        (TemplateVersion.DoesNotExist, 404),
        (ValueError, 400),
    ],
)
def test_download_template_errors(
    db, mocker, clients, template_versions, exc, status_code
):
    """
    Test download_templates errors
    """
    client = clients.get("Administrators")
    mock_study_pkg = mocker.patch(
        "creator.data_templates.views.template_package", side_effect=exc()
    )
    # With study
    study = template_versions[0].studies.first()
    resp = client.get(f"/download/templates/{study.pk}")
    assert resp.status_code == status_code

    # Without study
    resp = client.get("/download/templates")
    assert resp.status_code == status_code


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", True),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_download_templates_study(
    db, clients, template_versions, user_group, allowed
):
    """
    Test download_templates with a given study
    """
    client = clients.get(user_group)
    study = template_versions[0].studies.first()
    resp = client.get(f"/download/templates/{study.pk}")

    if allowed:
        filename = f"{study.pk}_templates.xlsx"
        assert resp.status_code == 200
        assert resp.get("Content-Disposition") == (
            f"attachment; filename*=UTF-8''{filename}"
        )
        assert resp.get("Content-Length")
        assert pandas.read_excel(BytesIO(resp.content), sheet_name=None)

        # Check appropriate event fired
        template_events = Event.objects.filter(event_type="TV_DOW").all()
        assert len(template_events) == 1
        for tv in study.template_versions.all():
            assert tv.pk in template_events[0].description
    else:
        assert resp.status_code == 401


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", True),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
def test_download_templates_no_study(
    db, clients, template_versions_mult_studies, user_group, allowed
):
    """
    Test download_templates without a study given
    """
    client = clients.get(user_group)
    tv_string = ",".join(tv.pk for tv in template_versions_mult_studies)
    params = {"template_versions": tv_string}
    resp = client.get("/download/templates", params)

    if allowed:
        filename = "template_package.xlsx"
        assert resp.status_code == 200
        assert resp.get("Content-Disposition") == (
            f"attachment; filename*=UTF-8''{filename}"
        )
        assert resp.get("Content-Length")
        assert pandas.read_excel(BytesIO(resp.content), sheet_name=None)

        # Check appropriate events fired
        template_events = Event.objects.filter(event_type="TV_DOW").all()
        assert len(template_events) == 1
        for tv in template_versions_mult_studies:
            assert tv.pk in template_events[0].description
    else:
        assert resp.status_code == 401


@pytest.mark.parametrize(
    "file_format,ext,mime_type,filter_templates",
    [
        ("excel", ".xlsx", XLSX_MIME_TYPE, True),
        ("zip", ".zip", ZIP_MIME_TYPE, True),
        (None, ".xlsx", XLSX_MIME_TYPE, True),
        (None, ".xlsx", XLSX_MIME_TYPE, False),
    ],
)
def test_download_templates_query_params(
    db,
    mocker,
    clients,
    template_versions,
    file_format,
    ext,
    mime_type,
    filter_templates,
):
    """
    Test download_templates with query params
    """
    mock_study_pkg = mocker.patch(
        "creator.data_templates.views.template_package",
        return_value=(BytesIO(), template_versions),
    )
    client = clients.get("Administrators")

    # Add query params
    params = {}
    if file_format:
        params["file_format"] = file_format
    if filter_templates:
        tv_ids = ",".join([tv.pk for tv in template_versions])
        params["template_versions"] = tv_ids

    study = template_versions[0].studies.first()
    resp = client.get(f"/download/templates/{study.pk}", params)

    # Check response
    assert resp.status_code == 200
    filename = f"{study.pk}_templates{ext}"
    assert resp.get("Content-Disposition") == (
        f"attachment; filename*=UTF-8''{filename}"
    )
    assert resp.get("Content-Type") == mime_type

    # Check call args study_template_package
    # args = mock_study_pkg.call_args.args
    kwargs = mock_study_pkg.call_args.kwargs
    # assert args[0] == study.pk
    assert kwargs["study_kf_id"] == study.pk
    if not file_format:
        file_format = "excel"
    assert kwargs["excel_workbook"] == (file_format == "excel")
    if filter_templates:
        assert set(kwargs["template_version_ids"]) == set(tv_ids.split(","))


def test_download_single_template_filenames(db, clients, template_versions):
    """
    When a single DataTemplate is downloaded, the filename should incorporate
    that template's ID.
    """
    client = clients.get("Administrators")
    # A single template (no study), excel format
    params = {"template_versions": f"{template_versions[0].pk}"}
    resp = client.get("/download/templates", params)
    excel_filename = f"{template_versions[0].pk}_template.xlsx"
    assert resp.get("Content-Disposition") == (
        f"attachment; filename*=UTF-8''{excel_filename}"
    )

    # Same as above but archive format
    params["file_format"] = "zip"
    resp = client.get("/download/templates", params)
    zip_filename = f"{template_versions[0].pk}_template.zip"
    assert resp.get("Content-Disposition") == (
        f"attachment; filename*=UTF-8''{zip_filename}"
    )

    # A single template with study, excel
    study = template_versions[0].studies.first()
    params = {"template_versions": f"{template_versions[0].pk}"}
    resp = client.get(f"/download/templates/{study.pk}", params)
    assert resp.get("Content-Disposition") == (
        f"attachment; filename*=UTF-8''{excel_filename}"
    )

    # A single template with study, archive
    params["file_format"] = "zip"
    resp = client.get("/download/templates", params)
    assert resp.get("Content-Disposition") == (
        f"attachment; filename*=UTF-8''{zip_filename}"
    )
