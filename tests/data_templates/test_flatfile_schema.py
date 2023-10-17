import os
import json
import pytest
import pandas

from marshmallow import ValidationError
from pprint import pprint

from creator.data_templates.factories import TemplateVersionFactory
from creator.data_templates.models import TemplateVersion
from creator.data_templates.flatfile_settings_schema import (
    NO_MATCH_OPTION,
    snake_to_camel,
    FlatfileFieldSchema,
    FlatfileSettingsSchema
)


@pytest.mark.parametrize(
    "in_value, expected_out",
    [
        ("config_setting", "configSetting"),
        ("Config_Setting", "configSetting"),
    ]
)
def test_snake_to_camel(in_value, expected_out):
    """
    Test helper function snake_to_camel
    """
    assert snake_to_camel(in_value) == expected_out


def test_remove_duplicates(mocker):
    """
    Test FlatfileSettingsSchema.remove_duplicates
    """
    mock_logger = mocker.patch(
        "creator.data_templates.flatfile_settings_schema.logger"
    )
    # No duplicate fields
    data = {
        "fields": [
            {"key": f"CONCEPT {i}", "label": f"My column {i}"}
            for i in range(3)
        ]
    }
    schema = FlatfileSettingsSchema()
    data = schema.remove_duplicates(data)
    assert mock_logger.warning.call_count == 0
    assert len(data["fields"]) == 3
    mock_logger.reset_mock()

    # Duplicate fields
    data = {
        "fields": [
            {"key": "CONCEPT A", "label": f"My column {i}"}
            for i in range(3)
        ]
    }
    schema = FlatfileSettingsSchema()
    data = schema.remove_duplicates(data)
    assert mock_logger.warning.call_count == 2
    assert len(data["fields"]) == 1


def test_flatfile_settings_load(db):
    """
    Test FlatfileSettingsSchema.load
    """
    fields = TemplateVersionFactory().field_definitions["fields"]
    data = {"fields": fields, "title": "Upload Docs", "type": "Data"}
    settings = FlatfileSettingsSchema().load(data)
    assert settings
    assert all(k[0].islower() for k in settings)


def test_flatfile_field_preload(db):
    """
    Test FlatfileFieldSchema.from_template_field preload function
    """
    tv = TemplateVersionFactory()
    tv.clean()
    field = tv.field_definitions["fields"][0]
    schema = FlatfileFieldSchema()

    # Test select
    out = schema.from_template_field(field)
    assert out["key"] == field["label"]
    assert out["label"] == field["label"]
    assert out["description"] == field["description"]
    assert out["type"] == "select"
    for option in [
        {"label": "a", "value": "a"},
        {"label": "b", "value": "b"},
        {"label": "c", "value": "c"},
        {
            "label": NO_MATCH_OPTION,
            "value": "_".join(NO_MATCH_OPTION.split(" ")).lower()
        },
    ]:
        assert option in out["options"]

    assert "match_strategy" in out

    # Test checkbox
    out = schema.from_template_field(
        {"key": "k", "label": "l", "data_type": "boolean"}
    )
    assert out["type"] == "checkbox"
    assert "options" not in out

    # Test other types
    out = schema.from_template_field(
        {"key": "k", "label": "l", "data_type": "string"}
    )
    assert "type" not in out
    assert "options" not in out


def test_flatfile_field_load(db):
    """
    Test FlatfileFieldSchema.load
    """
    field = TemplateVersionFactory().field_definitions["fields"][0]
    ff_field = FlatfileFieldSchema().load(field)
    assert ff_field
