from typing import Union

import pandas
from marshmallow import (
    fields, validate, pre_load, post_load, Schema, ValidationError, EXCLUDE
)
from kf_lib_data_ingest.common.misc import multisplit
from kf_lib_data_ingest.common.io import read_df
from pprint import pprint, pformat


def coerce_number(
    input_value: Union[str, int, float, bool, None]
) -> Union[int, float, str, None]:
    """
    Try to coerce a str literal to an int/float

    If coercion is not possible return the original input value
    """
    # Don't try to convert None or values that are already numeric
    # in order to preserve precision
    if input_value is None:
        return input_value

    if isinstance(input_value, (int, float)):
        return input_value

    i_value = None
    f_value = None
    try:
        f_value = float(input_value)
        i_value = int(input_value)
    except ValueError:
        pass

    # Input was a non-coercable str
    if (i_value is None) and (f_value is None):
        new_value = input_value
    # Input was an int
    elif i_value == f_value:
        new_value = i_value
    # Input was a float
    else:
        new_value = f_value

    return new_value


def coerce_bool(
    input_value: Union[bool, str, int, float, None]
) -> Union[bool, str, None]:
    """
    Try to coerce a str literal to a boolean
    Coercion will include attempting to translate str synonyms to booleans

    If coercion is not possible return the original input value
    """
    input_value = coerce_number(input_value)

    if isinstance(input_value, str):
        alternates = {
            "true": True,
            "false": False,
            "yes": True,
            "no": False,
            "required": True,
            "not required": False,
        }
        new_value = alternates.get(input_value.lower(), input_value)
    else:
        try:
            new_value = bool(input_value)
        except ValueError as e:
            new_value = input_value

    return new_value


class FieldDefinitionSchema(Schema):
    """
    Marshmallow schema for a cleaning and validating a JSON object
    containing a field definition instance in TemplateVersion.field_definitions

    Notes:
        The missing kwarg is used when the marshmallow field key is not present
        in the input data and marshmallow needs to know if it should insert
        the key with some kind of value

        The allow_none kwarg is used when you want to allow the field to take
        on a None value
    """
    key = fields.String(
        description="Canonical name or identifier for the field",
        missing=None,
        allow_none=None
    )
    label = fields.String(
        description="Human friendly name for the field",
        required=True
    )
    data_type = fields.String(
        description="The data type of this field's values",
        validate=validate.OneOf(
            ['enum', 'string', 'number', 'boolean', 'date']
        ),
        missing="string"
    )
    required = fields.Boolean(
        description="Whether the field is required to be populated",
        missing=False
    )
    accepted_values = fields.List(
        fields.Raw(),
        description="The list of acceptable values this field may be"
                    "populated with",
        # This says, if accepted_values is not None, then make sure it has
        # at least one member in the list
        validate=validate.Length(min=1),
        missing=None,
        allow_none=True
    )
    missing_values = fields.List(
        fields.String(allow_none=True),
        description="Values that a submitter may use if the data for this "
        "field is unknown or unavailable for whatever reason",
        # This says, if missing_values is not None, then make sure it has
        # at least one member in the list
        validate=validate.Length(min=1),

        # If this is None, then we will interpret this to mean there are no
        # defined missing values
        missing=None,
        allow_none=True
    )
    description = fields.String(
        description="Description for the field",
        required=True
    )
    instructions = fields.String(
        description="Instructions or best practices for the data submitter "
                    "on how to populate this field",
        missing=None,
        allow_none=True
    )

    class Meta:
        # Maintain ordering of keys
        ordered = True
        # Exclude unknown fields from output
        unknown = EXCLUDE

    @pre_load
    def clean(self, in_data, **kwargs):
        """
        Do our best to clean and correct any human errors or variability in
        the input data before the it is validated against the schema
        """
        out_data = {}
        for k, v in in_data.items():
            # Title case to snake case
            k = "_".join(k.strip().lower().split(" "))

            # Strip white space
            if isinstance(v, str):
                v = v.strip() or None  # interpret empty str as null

            # Convert str synonyms to booleans
            if k == "required":
                out_data[k] = coerce_bool(v)

            # Lower case value in data_type
            elif k == "data_type":
                if not v:
                    v = self.fields[k].missing
                out_data[k] = str(v).strip().lower()

            # Convert delimited str to list
            elif k == "accepted_values" and isinstance(v, str):
                values = multisplit(v, [",", ";", "\n"])
                out_data[k] = [val.strip() for val in values if val.strip()]

            elif k == "missing_values" and isinstance(v, str):
                values = multisplit(v, [",", ";", "\n"])
                out_data[k] = [val.strip() for val in values if val.strip()]
            else:
                out_data[k] = v

        if out_data.get("accepted_values"):
            out_data["data_type"] = "enum"

        return out_data


class FieldDefinitionsSchema(Schema):
    """
    Marshmallow schema for a cleaning and validating a list of field
    definition objects in TemplateVersion.field_definitions
    """
    version = {
        "number": "0.1.0",
        "changes": "Initial version"
    }
    key_order = list(FieldDefinitionSchema().fields.keys())

    fields = fields.List(
        fields.Nested(FieldDefinitionSchema),
        description="List of field definitions for a data template",
        required=True,
        validate=validate.Length(min=1)
    )

    @post_load
    def add_version(self, data, **kwargs):
        """
        Add a section for the schema version so that consumers know if the
        schema changed
        """
        data.update({"schema_version": self.version})
        return data

    def handle_error(self, exc, data, **kwargs):
        """
        Reformat ValidationError message to be more user friendly

        Field definition errors will be keyed by the field definition's label
        (e.g. column name) rather than its index in the list of input field
        definitions

        Example:
            Normal Error:
                {
                    "fields": 0: [errors here],
                    "fields": 1: [errors here],
                    "fields": 2: [errors here],
                }

            Formatted Error:
                {
                    "Field Definition [Person ID]": [errors here],
                    "Field Definition [1]": [errors here],
                    "Field Definition [Specimen ID]": [errors here]
                }

        If anything goes wrong in reformatting, just return original exception
        """
        formatted_errors = {}
        try:
            input_fields = data.get("fields")
            error_fields = exc.messages.get("fields")
            for idx, errors in error_fields.items():
                field = input_fields[int(idx)]
                field_name = field.get("Label") or field.get("label")
                field_name = field_name or idx
                formatted_errors[f"Field Definition [{field_name}]"] = errors
        except Exception:
            # If anything unexpected happens, just pass here and
            # raise the original exception
            pass

        if formatted_errors:
            raise ValidationError(pformat(formatted_errors))
        else:
            raise exc
