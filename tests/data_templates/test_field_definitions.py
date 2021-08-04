import os
import json
import pytest
import pandas

from marshmallow import ValidationError
from pprint import pprint

from creator.data_templates.models import TemplateVersion
from creator.data_templates.field_definitions_schema import (
    coerce_number,
    coerce_bool,
    FieldDefinitionSchema,
    FieldDefinitionsSchema
)


@pytest.mark.parametrize(
    "in_value, expected_out",
    [
        ("0.0", 0.0),
        (0.0, 0.0),
        ("0", 0),
        (0, 0),
        ("10.0", 10),
        (10.0, 10),
        ("200", 200),
        (200, 200),
        ("1.234", 1.234),
        (1.234, 1.234),
        ("foo", "foo"),
        (None, None),
    ]
)
def test_coerce_number(in_value, expected_out):
    """
    Test helper function that coerces strings to float/int
    """
    assert coerce_number(in_value) == expected_out


@pytest.mark.parametrize(
    "in_value, expected_out",
    [
        (True, True),
        (False, False),
        ("foo", "foo"),
        ("0.0", False),
        ("1", True),
        ("True", True),
        ("FALSE", False),
        ("Yes", True),
        ("no", False),
        ("Required", True),
        ("Not Required", False),
        (None, False),
    ]
)
def test_coerce_bool(in_value, expected_out):
    """
    Test helper function that coerces strings to booleans
    """
    assert coerce_bool(in_value) == expected_out


def test_schema_clean():
    """
    Test FieldDefinitionSchema.clean method
    """
    schema = FieldDefinitionSchema()

    # Test keys are all snake cased
    in_data = {
        "Label": None,
        "Data Type": None,
    }
    out_data = schema.clean(in_data)
    assert {"label", "data_type"} == set(out_data.keys())

    # Test data_type default
    assert out_data["data_type"] == "string"

    # Test data_type casing
    in_data["data_type"] = "Number"
    out_data = schema.clean(in_data)
    assert out_data["data_type"] == "number"

    # Test accepted_values
    in_data["accepted_values"] = None
    out_data = schema.clean(in_data)
    assert out_data["accepted_values"] is None

    in_data["data_type"] = "foobar"
    in_data["accepted_values"] = "1.0, 2.0, 3.0"
    out_data = schema.clean(in_data)
    assert out_data["accepted_values"] == ["1.0", "2.0", "3.0"]
    assert out_data["data_type"] == "enum"

    # Test missing values
    in_data["missing_values"] = None
    out_data = schema.clean(in_data)
    assert out_data["missing_values"] is None

    in_data["missing_values"] = "None, Unknown"
    out_data = schema.clean(in_data)
    assert ["None", "Unknown"] == out_data["missing_values"]

    # Test empty strings handled properly
    in_data["accepted_values"] = " "
    in_data["missing_values"] = ""
    in_data["required"] = " "
    in_data["data_type"] = "   "
    out_data = schema.clean(in_data)
    assert out_data["accepted_values"] is None
    assert out_data["missing_values"] is None
    assert out_data["required"] == False  # noqa
    assert out_data["data_type"] == "string"


def test_validation_error():
    """
    Test custom handling of validation errors
    """
    in_fields = {
        "fields": [
            {
                "Key": "person.id",
                "Label": "Person ID",
                # Missing description, but has required keys
            },
            {
                "Key": "specimen.id",
                "Description": "Identifier for specimen"
                # Missing label but has other required keys
            }
        ]
    }
    schema = FieldDefinitionsSchema()

    # Test custom validation message
    with pytest.raises(ValidationError) as e:
        schema.load(in_fields)
    errors = e.value.messages[0]
    assert "fields" not in errors
    assert "Field Definition [1]" in errors
    assert "Field Definition [Person ID]" in errors

    # Test normal validation message
    with pytest.raises(ValidationError) as e:
        schema.load("foo")
    assert {'_schema': ['Invalid input type.']} == e.value.messages


def test_schema_load():
    """
    End to end test using the field definitions schema to clean and validate
    input data
    """
    in_fields = {
        "fields": [
            {
                "Key": "person.id",
                "Label": "Person ID",
                "Description": "Identifier for person"
            },
            {
                "Key": "specimen.id",
                "Label": "Specimen ID",
                "Description": "Identifier for specimen"
            }
        ]
    }

    schema = FieldDefinitionsSchema()
    data = schema.load(in_fields)
    out_fields = data["fields"]

    # Check version
    assert data["schema_version"]["number"] == schema.SCHEMA_VERSION["number"]

    # Check all fields are in output
    assert len(out_fields) == len(in_fields["fields"])

    # Check that defaults were set right and all components of a field
    # definition are present in each field definition instance
    for out in out_fields:
        assert set(FieldDefinitionsSchema.key_order) == set(out.keys())
        assert out["data_type"] == "string"
        assert out["required"] == False  # noqa
        assert out["accepted_values"] is None
        assert out["instructions"]is None
