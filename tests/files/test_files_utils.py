from io import BytesIO

import pandas
from django.core.files import File

from creator.data_templates.factories import TemplateVersionFactory
from creator.files.factories import VersionFactory
from creator.files.utils import evaluate_template_match


def update_version_content(df, file_version):
    """
    Helper to update the file version's content
    """
    stream = BytesIO()
    df.to_csv(stream, sep="\t", index=False)
    stream.seek(0)
    file_version.key.save("data.tsv", File(stream))


def column_sets(template_version):
    """
    Helper to get required and optional cols from a template
    """
    required = set()
    optional = set()
    for f in template_version.field_definitions["fields"]:
        if f["required"]:
            required.add(f["label"])
        else:
            optional.add(f["label"])
    return required, optional


def test_version_matches_template(db):
    """
    Test computed property Version.matches_template
    """
    # Create a file version that matches a study template
    # File version should match template
    file_version = VersionFactory()
    tv = TemplateVersionFactory(studies=[file_version.root_file.study])
    update_version_content(tv.template_dataframe, file_version)
    file_version.root_file.template_version = tv
    assert file_version.matches_template

    # Missing template, then file should not match template
    file_version.root_file.template_version = None
    assert not file_version.matches_template

    # Missing root_file, then file should not match template
    file_version.root_file = None
    assert not file_version.matches_template


def test_evaluate_template_match(db):
    """
    Test evaluate_template_match
    """
    # Make two templates with same fields
    file_version = VersionFactory()
    template_versions = TemplateVersionFactory.create_batch(
        2, studies=[file_version.root_file.study]
    )
    tv = template_versions[0]

    update_version_content(tv.template_dataframe, file_version)
    results = evaluate_template_match(file_version, tv)

    # Since the file = template, everything should match
    required, optional = column_sets(tv)
    assert results["matches_template"]
    assert set(results["matched_required_cols"]) == set(required)
    assert set(results["matched_optional_cols"]) == set(optional)
    assert len(results["missing_optional_cols"]) == 0
    assert len(results["missing_required_cols"]) == 0

    # Make all columns optional, and set content of file = template
    for f in tv.field_definitions["fields"]:
        f["required"] = False

    update_version_content(tv.template_dataframe, file_version)
    results = evaluate_template_match(file_version, tv)

    # Everything should still match
    required, optional = column_sets(tv)
    assert results["matches_template"]
    assert set(results["matched_required_cols"]) == set(required)
    assert set(results["matched_optional_cols"]) == set(optional)
    assert len(results["missing_optional_cols"]) == 0
    assert len(results["missing_required_cols"]) == 0

    # Add a required col to the template
    tv.field_definitions["fields"].append(
        {
            "label": "foo",
            "required": True,
            "description": "my label"
        }
    )
    update_version_content(tv.template_dataframe, file_version)
    results = evaluate_template_match(file_version, tv)

    # Now we should see a missing required col
    required, optional = column_sets(tv)
    assert not results["matches_template"]
    assert set(results["matched_required_cols"]) == set(required) - {"foo"}
    assert set(results["matched_optional_cols"]) == set(optional)
    assert len(results["missing_required_cols"]) == 1

    # Test a template with only optional columns
    tv.field_definitions["fields"] = [
        {
            "label": "bar",
            "required": False,
            "description": "my label"
        }
    ]
    update_version_content(pandas.DataFrame({"a": [1]}), file_version)
    results = evaluate_template_match(file_version, tv)

    # No match - due to missing optional col
    required, optional = column_sets(tv)
    assert not results["matches_template"]
    assert len(results["matched_required_cols"]) == 0
    assert len(results["matched_optional_cols"]) == 0
    assert len(results["missing_required_cols"]) == 0
    assert set(results["missing_optional_cols"]) == set(["bar"])
