from io import StringIO
import os
import json
import pandas

from creator.studies.factories import StudyFactory
from creator.organizations.factories import OrganizationFactory
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory,
    TemplateVersion,
)
from creator.data_templates.field_definitions_schema import (
    FieldDefinitionsSchema
)


def test_template_released(db):
    """
    Test TemplateVersion.released property
    """
    # TemplateVersions that have studies should have released = True
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org)
    dt = DataTemplateFactory(organization=org)
    tv = TemplateVersionFactory(studies=studies)
    tv.refresh_from_db()
    assert tv.released == True  # noqa

    # TemplateVersions that have 0 studies should have released = False
    tv.studies.set([])
    tv.save()
    assert tv.released == False  # noqa


def test_template_dataframe(db):
    """
    Test the template_dataframe property on TemplateVersion instances
    """
    dt = DataTemplateFactory()
    tv = TemplateVersionFactory(data_template=dt)
    tv.clean()
    df = tv.template_dataframe
    assert isinstance(df, pandas.DataFrame)
    assert set(df.columns) == set(
        f["label"] for f in tv.field_definitions["fields"]
    )


def test_field_definitions_dataframe(db):
    """
    Test the field_definitions_dataframe property on TemplateVersion instances
    """
    dt = DataTemplateFactory()
    tv = TemplateVersionFactory(data_template=dt)
    tv.clean()
    df = tv.field_definitions_dataframe
    assert isinstance(df, pandas.DataFrame)
    assert set(df.columns) == set(
        " ".join(c.split("_")).title()
        for c in FieldDefinitionsSchema.key_order
        if c != "key"
    )
    assert df.shape == (2, len(FieldDefinitionsSchema.key_order) - 1)
    assert set(df["Accepted Values"].values.tolist()) == {"a,b,c"}


def test_load_field_definitions(db, tmpdir):
    """
    Test TemplateVersion.load_field_definitions
    """
    def check_fields(field_defs):
        field = field_defs["fields"][0]
        assert len(field_defs["fields"]) == 1
        assert set(FieldDefinitionsSchema.key_order) == set(field.keys())

    temp_dir = tmpdir.mkdir("test")

    # Test tabular file
    fp = os.path.join(temp_dir, "template.tsv")
    data = {
        "Label": "Person ID",
        "Description": "Identifier for person",
        "data_type": "enum",
        "accepted_values": "1\n2\n3",
        "instructions": ""
    }
    df = pandas.DataFrame([data]).to_csv(fp, sep="\t", index=False)
    field_defs = TemplateVersion.load_field_definitions(fp)
    check_fields(field_defs)

    # Test JSON file
    fp = os.path.join(temp_dir, "fields.json")
    data = {
        "Label": "Person ID",
        "Description": "Identifier for person",
        "data_type": "enum",
        "accepted_values": "1\n2\n3",
        "instructions": ""
    }
    with open(fp, "w") as json_file:
        json.dump({"fields": [data]}, json_file)

    field_defs = TemplateVersion.load_field_definitions(fp)
    check_fields(field_defs)

    # Test JSON file-like obj
    s = StringIO()
    json.dump({"fields": [data]}, s)
    s.seek(0)
    field_defs = TemplateVersion.load_field_definitions(
        s, original_name=os.path.basename(fp)
    )
    check_fields(field_defs)
    s.close()
