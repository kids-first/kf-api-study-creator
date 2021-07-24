from io import StringIO
import os
import json
import pytest
from graphql import GraphQLError
from marshmallow import ValidationError

from creator.data_templates.models import TemplateVersion

FIELDS = {"fields": [
    {
        "key": "person.id",
        "label": "Person ID",
        "description": "Person identifiers",
        "required": True,
        "data_type": "string",
        "instructions": f"Populate person id properly",
    }
]}

UPLOAD_FIELDS_MUTATION = """
    mutation ($file: Upload!) {
      uploadFieldDefinitions(file:$file) {
        success
        fileName
        fileSize
        fieldDefinitions
      }
    }
"""


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["change_datatemplate"], True),
        ([], False),
    ],
)
def test_upload_field_definitions(
    db, tmpdir, permission_client, permissions, allowed
):
    """
    Test the upload field definition mutation

    Users without the change_datatemplate permission should not be allowed
    to upload field definitions
    """
    user, client = permission_client(permissions)

    # Make temp file and upload it
    fields_file = os.path.join(tmpdir.mkdir("test"), "fields.json")
    with open(fields_file, "w+") as json_file:
        json.dump(FIELDS, json_file)
        json_file.seek(0)
        data = {
            "operations": json.dumps(
                {
                    "query": UPLOAD_FIELDS_MUTATION.strip(),
                    "variables":  {"file": None}
                }
            ),
            "file": json_file,
            "map": json.dumps({"file": ["variables.file"]}),
        }
        resp = client.post("/graphql", data=data)

    # Check response
    if allowed:
        result = resp.json()["data"]["uploadFieldDefinitions"]
        assert result["fileName"] == os.path.basename(fields_file)
        assert result["fileSize"] == os.stat(fields_file).st_size
        out_fields = json.loads(result["fieldDefinitions"])
        assert len(out_fields["fields"]) == len(FIELDS["fields"])
    else:
        assert "Not allowed" in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "exc,error_msg",
    [
        (ValidationError, "validation error"),
        (Exception, "went wrong while importing")
    ]
)
def test_upload_field_definitions_errors(
    db, mocker, tmpdir, permission_client, exc, error_msg
):
    """
    Test error cases in upload field definition mutation
    """
    user, client = permission_client(["change_datatemplate"])
    mock_load_fields = mocker.patch(
        "creator.data_templates.mutations.template_version"
        ".TemplateVersion.load_field_definitions",
        side_effect=exc(error_msg)
    )

    # Make temp file and upload it
    fields_file = os.path.join(tmpdir.mkdir("test"), "fields.json")
    with open(fields_file, "w+") as json_file:
        json.dump(FIELDS, json_file)
        json_file.seek(0)
        data = {
            "operations": json.dumps(
                {
                    "query": UPLOAD_FIELDS_MUTATION.strip(),
                    "variables":  {"file": None}
                }
            ),
            "file": json_file,
            "map": json.dumps({"file": ["variables.file"]}),
        }
        resp = client.post("/graphql", data=data)

    assert mock_load_fields.call_count == 1
    assert error_msg in resp.json()["errors"][0]["message"]


def test_file_too_large(db, tmpdir, settings, permission_client):
    """
    Test upload mutation when field definitions file is too large
    """
    user, client = permission_client(["change_datatemplate"])
    settings.FILE_MAX_SIZE = 1

    # Make temp file and upload it
    fields_file = os.path.join(tmpdir.mkdir("test"), "fields.json")
    with open(fields_file, "w+") as json_file:
        json.dump(FIELDS, json_file)
        json_file.seek(0)
        data = {
            "operations": json.dumps(
                {
                    "query": UPLOAD_FIELDS_MUTATION.strip(),
                    "variables":  {"file": None}
                }
            ),
            "file": json_file,
            "map": json.dumps({"file": ["variables.file"]}),
        }
        resp = client.post("/graphql", data=data)

    assert "exceeds max size" in resp.json()["errors"][0]["message"]
