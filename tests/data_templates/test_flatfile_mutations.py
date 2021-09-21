import pytest
import json
import uuid
from graphql_relay import to_global_id, from_global_id
from graphql import GraphQLError
from marshmallow import ValidationError

from creator.data_templates.models import TemplateVersion
from creator.data_templates.factories import TemplateVersionFactory
from creator.data_templates.mutations.flatfile import check_templates
from creator.data_templates.default_templates import default_templates


CREATE_FLATFILE_SETTINGS = """
mutation ($templateVersions: [ID]) {
    createFlatfileSettings(templateVersions: $templateVersions) {
        flatfileSettings
    }
}
"""


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["view_datatemplate"], True),
        ([], False),
    ],
)
def test_create_flatfile_settings(
    db, settings, permission_client, permissions, allowed
):
    """
    Test the create flatfile settings mutation

    Users without the view_datatemplate permission should not be allowed
    to create flatfile settings
    """
    user, client = permission_client(permissions)
    tvs = TemplateVersionFactory.create_batch(2)

    variables = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t.pk) for t in tvs
        ],
    }
    resp = client.post(
        "/graphql",
        data={"query": CREATE_FLATFILE_SETTINGS, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        resp_data = resp.json()["data"]["createFlatfileSettings"][
            "flatfileSettings"
        ]
        assert resp_data is not None

        # Check creation
        ff_settings = json.loads(resp_data)
        assert ff_settings["title"] == (
            f"Upload {settings.FLATFILE_DEFAULT_TYPE}"
        )
        assert ff_settings["type"] == (
            f"{settings.FLATFILE_DEFAULT_TYPE}"
        )
        fields = tvs[0].field_definitions["fields"]
        assert len(ff_settings["fields"]) == len(fields)

    else:
        assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_create_with_one_template(db, settings, permission_client):
    """
    Test the create mutation with one template
    """
    user, client = permission_client(["view_datatemplate"])
    tv = TemplateVersionFactory()

    variables = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t.pk) for t in [tv]
        ],
    }
    resp = client.post(
        "/graphql",
        data={"query": CREATE_FLATFILE_SETTINGS, "variables": variables},
        content_type="application/json",
    )

    resp_data = resp.json()["data"]["createFlatfileSettings"][
        "flatfileSettings"
    ]
    assert resp_data is not None

    # Check creation
    ff_settings = json.loads(resp_data)
    assert ff_settings["title"] == (
        f"Upload {tv.data_template.name} Data"
    )
    assert ff_settings["type"] == (
        f"{tv.data_template.name} Data"
    )
    fields = tv.field_definitions["fields"]
    assert len(ff_settings["fields"]) == len(fields)


def test_create_default_templates(db, permission_client):
    """
    Test the create mutation using default templates
    """
    user, client = permission_client(["view_datatemplate"])

    resp = client.post(
        "/graphql",
        data={"query": CREATE_FLATFILE_SETTINGS},
        content_type="application/json",
    )

    resp_data = resp.json()["data"]["createFlatfileSettings"][
        "flatfileSettings"
    ]
    assert resp_data is not None

    # Check creation
    ff_settings = json.loads(resp_data)
    assert ff_settings["fields"]


def test_create_template_not_found(db, permission_client):
    """
    Test the create mutation with a template that doesn't exist
    """
    user, client = permission_client(["view_datatemplate"])
    tv = TemplateVersionFactory()

    variables = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", str(uuid.uuid4()))
        ],
    }
    resp = client.post(
        "/graphql",
        data={"query": CREATE_FLATFILE_SETTINGS, "variables": variables},
        content_type="application/json",
    )
    assert "do not exist" in resp.json()["errors"][0]["message"]


def test_create_validation_error(db, mocker, permission_client):
    """
    Test the create mutation with invalid fields
    """
    mock_schema = mocker.patch(
        "creator.data_templates.mutations.flatfile.flatfile_schema"
    )
    mock_schema.load.side_effect = ValidationError("validation error")
    user, client = permission_client(["view_datatemplate"])
    tv = TemplateVersionFactory()

    variables = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t.pk) for t in [tv]
        ],
    }
    resp = client.post(
        "/graphql",
        data={"query": CREATE_FLATFILE_SETTINGS, "variables": variables},
        content_type="application/json",
    )
    assert "validation error" in resp.json()["errors"][0]["message"]


def test_create_general_exception(db, mocker, permission_client):
    """
    Test the create mutation with random error
    """
    mock_schema = mocker.patch(
        "creator.data_templates.mutations.flatfile.flatfile_schema"
    )
    mock_schema.load.side_effect = Exception("something weird")
    user, client = permission_client(["view_datatemplate"])
    tv = TemplateVersionFactory()

    variables = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t.pk) for t in [tv]
        ],
    }
    resp = client.post(
        "/graphql",
        data={"query": CREATE_FLATFILE_SETTINGS, "variables": variables},
        content_type="application/json",
    )
    assert "Unable to build" in resp.json()["errors"][0]["message"]


def test_check_template_versions(db):
    """
    Test helper function used in create mutation
    """
    # Normal case
    tv = TemplateVersionFactory()
    node_ids = [
        to_global_id("TemplateVersionNode", t.pk) for t in [tv]
    ]
    templates = check_templates(node_ids)
    for t in templates:
        assert t.pk

    # Template not found
    node_ids.append(
        to_global_id("TemplateVersionNode", str(uuid.uuid4()))
    )
    with pytest.raises(TemplateVersion.DoesNotExist) as e:
        check_templates(node_ids)
    assert "One or more template" in str(e)
