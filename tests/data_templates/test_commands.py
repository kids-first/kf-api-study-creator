import os
import pytest
from django.core import management

from creator.organizations.factories import OrganizationFactory, Organization
from creator.studies.factories import StudyFactory
from creator.data_templates.management.commands.faketemplates import (
    TEMPLATES_PATH,
    create_templates_from_workbook
)


def test_create_templates_from_workbook(db):
    """
    Test helper method create_templates_from_workbook
    """
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org)
    created = create_templates_from_workbook(TEMPLATES_PATH, org)
    tvs = [tv for s in studies for tv in s.template_versions.all()]
    assert set(tv.pk for tv in tvs) == set(tv.pk for tv in created)
    for tv in tvs:
        assert len(tv.field_definitions["fields"])


def test_faketemplates(db, mocker, tmpdir):
    """
    Test the faketemplates command
    """
    mock_create_templates = mocker.patch(
        "creator.data_templates.management.commands.faketemplates"
        ".create_templates_from_workbook"
    )
    mock_logger = mocker.patch(
        "creator.data_templates.management.commands.faketemplates.logger"
    )
    # Test defaults
    org = OrganizationFactory()
    management.call_command("faketemplates", org.name)
    msgs = [call.args[0] for call in mock_logger.info.call_args_list]
    assert "Deleted" in "\n".join(msgs)
    mock_create_templates.assert_called_with(TEMPLATES_PATH, org)

    for mock in [mock_create_templates, mock_logger]:
        mock.reset_mock()

    # Test non-defaults
    fp = os.path.join(tmpdir.mkdir("test"), "package.xlsx")
    with open(fp, "w") as package_file:
        package_file.write("the package")
    management.call_command(
        "faketemplates", org.name, delete=False, template_package=fp
    )
    msgs = [call.args[0] for call in mock_logger.info.call_args_list]
    assert "Deleted" not in "\n".join(msgs)
    mock_create_templates.assert_called_with(fp, org)


def test_faketemplates_errors(db, mocker):
    """
    Test the faketemplates command
    """
    mock_create_templates = mocker.patch(
        "creator.data_templates.management.commands.faketemplates"
        ".create_templates_from_workbook"
    )
    mock_logger = mocker.patch(
        "creator.data_templates.management.commands.faketemplates.logger"
    )
    with pytest.raises(Organization.DoesNotExist) as e:
        management.call_command("faketemplates", "foo")

    with pytest.raises(FileNotFoundError) as e:
        management.call_command(
            "faketemplates", OrganizationFactory().name, template_package="foo"
        )
