"""
Schemas for Flatfile settings JSON which is required
as input to the Flatfile Portal import button in the Data Tracker frontend app.

Flatfile settings are composed from the field definitions of
template versions. In most cases, the settings object will be
built from a list of study's templates.

A schema is not *needed* to convert templates to Flatfile settings, however,
Flatfile does not offer a serialized schema itself for validating the
settings. We define one here because it improves readability/understanding of
template to Flatfile settings serialization and provides a way for
the API to validate Flatfile settings.

*NOTE* The the Flatfile settings attributes included here only represent
a partial list of the settings attributes which we believe to be relevant
for our usage of Flatfile.

See https://flatfile.com/developers/javascript/getting-started/ for details
"""
import logging
from django.conf import settings

from marshmallow import (
    fields, validate, pre_load, post_load, Schema, ValidationError, EXCLUDE
)
from kf_lib_data_ingest.common.misc import multisplit
from kf_lib_data_ingest.common.io import read_df
from pprint import pformat

logger = logging.getLogger(__name__)

NO_MATCH_OPTION = "No matching value"


def snake_to_camel(in_str):
    """
    Convert snake_case to lower camelCase string
    """
    out = "".join(w.title() for w in in_str.split("_"))
    return out[0].lower() + out[1:]


class FlatfileFieldSchema(Schema):
    """
    Marshmallow schema for a Flatfile field

    See https://flatfile.com/developers/javascript/options/#fields
    """
    key = fields.String(
        description="Canonical name or identifier for the field",
        required=True
    )
    label = fields.String(
        description="Human friendly name for the field",
        required=True
    )
    type = fields.String(
        description="Type of UI element that should be rendered for the field",
        validate=validate.OneOf(['checkbox', 'select']),
    )
    description = fields.String(
        description="Description for the field",
    )
    validators = fields.List(
        fields.Dict(),
        description="How the field should be validated",
    )
    options = fields.List(
        fields.Dict(),
        description="List of acceptable values for the field if it is has "
        "type `select`",
    )
    match_strategy = fields.String(
        description="How the field option values should be matched",
        validate=validate.OneOf(['fuzzy', 'exact']),
    )

    class Meta:
        # Maintain ordering of keys
        ordered = True
        # Exclude unknown fields from output
        unknown = EXCLUDE

    @pre_load
    def from_template_field(self, template_field, **kwargs):
        """
        Convert a field dict in TemplateVersion.field_definitions to a
        Flatfile field dict

        See https://flatfile.com/developers/javascript/fields/
        """
        out_data = {}

        # Field key and label
        tlabel = template_field.get("label")
        out_data["label"] = tlabel
        # Use label as the key
        out_data["key"] = tlabel
        out_data["description"] = template_field.get("description")

        data_type = template_field.get("data_type")

        # Field type
        if data_type in {"enum", "boolean"}:
            type_mapping = {
                "boolean": "checkbox",
                "enum": "select"
            }
            out_data["type"] = type_mapping.get(data_type)

        # Field options
        if data_type == "enum":
            accepted_vals = template_field.get("accepted_values", []) or []
            missing_vals = template_field.get("missing_values", []) or []
            # NOTE: We need a workaround for Flatfile's limitation with
            # matching enum values. When a user has an enum value in their
            # file and cannot map it to any of the available enum values,
            # Flatfile doesn't allow the user to include their enum value
            # We will add an enum value that the user can select if their
            # value cannot be mapped to any of the available values
            options = [
                {"value": "_".join(val.split(" ")).lower(), "label": val}
                for val in set(
                    accepted_vals + missing_vals + [NO_MATCH_OPTION]
                )
            ]
            out_data["options"] = options

        # Field match strategy
        out_data["match_strategy"] = settings.FLATFILE_MATCH_STRATEGY

        return out_data

    @post_load
    def snake_to_camel(self, data, **kwargs):
        """
        Convert all keys in output to camel case
        """
        out_data = {}
        for k, v in data.items():
            out_data[snake_to_camel(k)] = v
        return out_data


class FlatfileSettingsSchema(Schema):
    """
    A Marshmallow schema for the Flatfile Settings object that is required
    as input to the Flatfile import button.


    *NOTE* The the Flatfile settings attributes included here only represent
    a partial list of the settings attributes which we believe to be relevant
    for our usage of Flatfile.

    See https://flatfile.com/developers/javascript/getting-started/ for details
    """
    allow_invalid_submit = fields.Boolean(
        description="Whether users will be able to submit data with errors",
        missing=settings.FLATFILE_ALLOW_INVALID_SUBMIT,
    )
    allow_custom = fields.Boolean(
        description="Whether users will be able to include columns that are "
        "not in the template's field definitions",
        missing=settings.FLATFILE_ALLOW_CUSTOM,
    )
    auto_detect_headers = fields.Boolean(
        description="Whether the header in tabular file will be auto detected",
        missing=settings.FLATFILE_AUTO_DETECT_HEADERS,
    )
    dev_mode = fields.Boolean(
        description="Determines whether charges will be incurred for Flatfile "
        "imports. If in dev mode no charges willl be incurred.",
        missing=settings.FLATFILE_DEV_MODE,
    )
    managed = fields.Boolean(
        description="Whether or not complex files (e.g. excel) should be "
        "processed in the browser or by the Flatfile service",
        missing=settings.FLATFILE_MANAGED,
    )
    title = fields.String(
        description="The title displayed on the Flatfile import "
        "modal (e.g. Upload SD_ME0WME0W Documents",
        missing=settings.FLATFILE_DEFAULT_TITLE
    )
    type = fields.String(
        description="A name or identifier for the category of settings",
        missing=settings.FLATFILE_DEFAULT_TYPE,
    )
    fields = fields.List(
        fields.Nested(FlatfileFieldSchema),
        description="List of Flatfile settings fields",
        required=True,
        validate=validate.Length(min=1)
    )

    def snake_to_camel(self, data):
        """
        Convert all keys in output to camel case
        """
        out_data = {}
        for k, v in data.items():
            out_data[snake_to_camel(k)] = v
        return out_data

    def remove_duplicates(self, data):
        """
        Remove fields that result in duplicate keys

        A field has a label and a key. The label is equivalent to a column in a
        template and the key is equivalent to a domain concept. Therefore it
        does not make sense to allow two different columns which mean the
        same thing.
        """
        logger.info("Begin building Flatfile settings object")
        fields = {}
        for f in data["fields"]:
            if f["key"] in fields:
                logger.warning(
                    f"Skipping duplicate field: {pformat(f)}. There is "
                    f"already a field: {f['label']} which maps to "
                    f"key: {f['key']}"
                )
            else:
                fields[f["key"]] = f
        data["fields"] = list(fields.values())
        return data

    @post_load
    def post_process(self, data, **kwargs):
        """
        Remove duplicate fields and camel case all keys in Flatfile settings
        object because the Flatfile expects camel cased keys

        See remove_duplicates
        """
        return self.snake_to_camel(self.remove_duplicates(data))
