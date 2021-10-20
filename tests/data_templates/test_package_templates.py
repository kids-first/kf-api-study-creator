import uuid
import pytest
import os
import zipfile
from io import BytesIO

import pandas

from creator.studies.factories import StudyFactory
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory,
)
from creator.data_templates.models import TemplateVersion
from creator.data_templates.packaging import (
    make_sheet_name,
    templates_to_excel_workbook,
    templates_to_archive,
    template_package,
)


@pytest.fixture
def template_versions(db):
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


def test_template_package_errors(db):
    """
    Test error cases in template_package
    """
    # One or more template versions does not exist, with study
    study = StudyFactory()
    dt = DataTemplateFactory(organization=study.organization)
    tv = TemplateVersionFactory(data_template=dt)
    template_version_ids = [str(uuid.uuid4), tv.pk]
    with pytest.raises(TemplateVersion.DoesNotExist) as e:
        template_package(study.pk, template_version_ids=template_version_ids)
    assert "One or more" in str(e)

    # One of more template versions does not exist, no study
    with pytest.raises(TemplateVersion.DoesNotExist) as e:
        template_package(template_version_ids=template_version_ids)
    assert "One or more" in str(e)

    # No input given
    with pytest.raises(ValueError) as e:
        template_package()
    assert "No input provided" in str(e)

    # Study does not have templates yet
    with pytest.raises(TemplateVersion.DoesNotExist) as e:
        template_package(study.pk)
    assert "No templates exist" in str(e)

    # Duplicate template names
    tvs = TemplateVersionFactory.create_batch(
        2, data_template=dt, studies=[study]
    )
    with pytest.raises(ValueError) as e:
        template_package(study.pk)
    assert "duplicate names" in str(e)


def test_template_package_success_study(db, mocker, template_versions):
    """
    Test template_package with a given study
    """
    mock_to_excel = mocker.patch(
        "creator.data_templates.packaging.templates_to_excel_workbook"
    )
    mock_to_archive = mocker.patch(
        "creator.data_templates.packaging.templates_to_archive"
    )
    tvs = template_versions

    # Test defaults
    study = tvs[0].studies.first()
    template_package(study.pk)
    fp = os.path.join(os.getcwd(), f"{study.pk}_templates")
    assert mock_to_excel.call_args.kwargs["filepath_or_buffer"] == fp
    assert {tv.pk for tv in mock_to_excel.call_args.args[0]} == {
        tv.pk for tv in tvs
    }

    # Test non-defaults
    template_package(
        study.pk,
        template_version_ids=[tv.pk for tv in tvs[:1]],
        filepath_or_buffer="foo",
        excel_workbook=False,
    )
    assert mock_to_archive.call_args.kwargs["filepath_or_buffer"] == "foo"
    assert {tv.pk for tv in mock_to_archive.call_args.args[0]} == {
        tv.pk for tv in tvs[:1]
    }

    # Test naming for single template, no filepath provided
    template_package(study.pk, template_version_ids=[tv.pk for tv in tvs[:1]])
    fp = os.path.join(os.getcwd(), f"{tvs[0].pk}_template")
    assert mock_to_excel.call_args.kwargs["filepath_or_buffer"] == fp


def test_template_package_success_no_study(
    db, mocker, template_versions_mult_studies
):
    """
    Test template_package without a study given
    """
    mock_to_excel = mocker.patch(
        "creator.data_templates.packaging.templates_to_excel_workbook"
    )
    mock_to_archive = mocker.patch(
        "creator.data_templates.packaging.templates_to_archive"
    )
    tvs = template_versions_mult_studies
    tv_ids = [tv.pk for tv in tvs]

    # Test defaults (need template versions at least)
    template_package(template_version_ids=tv_ids)
    fp = os.path.join(os.getcwd(), "template_package")
    assert mock_to_excel.call_args.kwargs["filepath_or_buffer"] == fp
    assert {tv.pk for tv in mock_to_excel.call_args.args[0]} == {
        tv.pk for tv in tvs
    }

    # Test non-defaults
    template_package(
        template_version_ids=tv_ids[:1],
        filepath_or_buffer="foo",
        excel_workbook=False,
    )
    assert mock_to_archive.call_args.kwargs["filepath_or_buffer"] == "foo"
    assert mock_to_archive.call_args.args[0][0].pk == tv_ids[0]


def test_templates_to_archive(db, mocker, tmpdir, template_versions):
    """
    Test templates_to_archive
    """
    tvs = template_versions

    # Test defaults
    mock_get_cwd = mocker.patch(
        "creator.data_templates.packaging.os.getcwd",
        return_value=tmpdir.mkdir("test"),
    )
    fp = templates_to_archive(tvs)
    assert mock_get_cwd.call_count == 1

    # Check its a valid zip file
    assert zipfile.is_zipfile(fp)
    assert "template_package.zip" == os.path.basename(fp)

    # Check files in zip file
    zf = zipfile.ZipFile(fp)
    toc_file = "template_package/table_of_contents.tsv"
    archive_file_list = [i.filename for i in zf.infolist()] + [toc_file]
    expected_file_list = [
        "template_package/"
        f"{'-'.join(tv.data_template.name.split(' ')).lower()}"
        f"-{type_}.tsv"
        for type_ in ["fields", "template"]
        for tv in tvs
    ]
    assert set(archive_file_list) == set(expected_file_list + [toc_file])

    # Check table of contents
    toc = pandas.read_csv(zf.open(toc_file), sep="\t")
    # Template names
    assert set(tv.data_template.name for tv in tvs) == set(
        toc["Template Name"].values.tolist()
    )
    # Template descriptions
    assert set(tv.data_template.description for tv in tvs) == set(
        toc["Template Description"].values.tolist()
    )
    # Template files
    file_list = []
    for files in toc["Files"].values.tolist():
        file_list.extend(files.split("\n"))
    expected_file_list = [os.path.basename(f) for f in expected_file_list]
    assert set(expected_file_list) == set(file_list)

    # Test non-defaults
    # Custom filepath
    in_fp = os.path.join(tmpdir.mkdir("test2"), "foobar.baz")
    fp = templates_to_archive(tvs, filepath_or_buffer=in_fp)
    assert fp.endswith("foobar.zip")
    zf = zipfile.ZipFile(fp)
    for info in zf.infolist():
        assert "foobar/" in info.filename
        assert info.file_size
    # Buffer
    buf = BytesIO()
    buf = templates_to_archive(tvs, filepath_or_buffer=buf)
    zf = zipfile.ZipFile(buf)
    for info in zf.infolist():
        assert "template_package/" in info.filename
        assert info.file_size


@pytest.mark.parametrize(
    "template_name,type_,expected_name",
    [
        ("My Template", "Template", "My Template - Template"),
        ("My Template", "Fields", "My Template - Fields"),
        (
            "Biospecimen Collection Manifest",
            "Fields",
            "Biospecimen Collection - Fields",
        ),
        (
            "Biospecimen Collection Manifest",
            "Template",
            "Biospecimen Collecti - Template",
        ),
    ],
)
def test_make_sheet_name(template_name, type_, expected_name):
    """
    Test helper function to make Excel sheet names
    """
    assert make_sheet_name(template_name, type_) == expected_name


def test_templates_to_excel(db, mocker, tmpdir, template_versions):
    """
    Test templates_to_excel_workbook
    """
    mock_get_cwd = mocker.patch(
        "creator.data_templates.packaging.os.getcwd",
        return_value=tmpdir.mkdir("test"),
    )

    tvs = template_versions
    fp = templates_to_excel_workbook(tvs)

    assert mock_get_cwd.call_count == 1

    # Check table of contents
    dfs = pandas.read_excel(fp, sheet_name=None)
    toc = dfs["Table of Contents"]
    # Template names
    assert set(tv.data_template.name for tv in tvs) == set(
        toc["Template Name"].values.tolist()
    )
    # Template descriptions
    assert set(tv.data_template.description for tv in tvs) == set(
        toc["Template Description"].values.tolist()
    )
    # Template files
    template_sheets = []
    for sheets in toc["Sheets"].values.tolist():
        template_sheets.extend(sheets.split("\n"))

    # Check all sheets exist
    sheet_names = pandas.ExcelFile(fp).sheet_names
    assert set(template_sheets + ["Table of Contents"]) == set(sheet_names)
