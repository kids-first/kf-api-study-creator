import logging
import django_rq
from django.conf import settings
from graphql import GraphQLError
from kf_lib_data_ingest.common.io import read_df

from creator.data_templates.models import TemplateVersion

logger = logging.getLogger(__name__)


def process_for_audit_submission(version, root_file=None):
    """
    Queue file version for audit submission if it is a valid file upload
    manifest
    """
    # This avoids circular import errors
    from creator.storage_analyses.tasks.expected_file import (
        prepare_audit_submission
    )
    if (
        root_file and
        settings.FEAT_DEWRANGLE_INTEGRATION and
        version.is_file_upload_manifest
    ):
        logger.info(
            f"Queued version {version.kf_id} {version.file_name} for"
            " audit processing..."
        )
        version.start_audit_prep()
        version.save()
        django_rq.enqueue(
            prepare_audit_submission, args=(version.pk, )
        )


def _file_columns(file_version):
    """
    Helper to get a file version's columns
    """
    from creator.analyses.analyzer import analyze_version
    from creator.analyses.models import Analysis

    analysis = None
    try:
        analysis = file_version.analysis
    except Analysis.DoesNotExist:
        pass
    # The file may not have had an analysis or has an analysis but it
    # has no columns due to it being an empty file at time of last analysis
    if not (analysis and analysis.columns):
        analysis = analyze_version(file_version)
        file_version.analysis = analysis
        file_version.analysis.save()

    return {c["name"].strip() for c in analysis.columns}


def evaluate_template_match(file_version, template_version):
    """
    Evaluate whether a file version matches a template and report the details
    of the mismatch between the file's columns and the template's
    required and optional columns.

    The file "matches" a template if the file contains all of the required
    columns in the template. If the template does not have any required
    columns defined, then a file "matches" a template if it contains all
    of the optional columns in the template.

    Return a dict that contains:
        - Whether or not the file version matches the template version
        - common columns between the file and the template's required columns
        - missing required columns in the file
        - common columns between the file and the template's optional columns
        - missing optional columns in the file

    Example:
    {
        "matches_template": False,
        "matched_required_cols": ["Subject ID", "Gender"],
        "missing_required_cols": ["Ethnicity", "Proband"],
        "matched_optional_cols": ["Race"]
        "missing_optional_cols": ["Vital Status"]
    }
    """
    results = {}
    file_columns = _file_columns(file_version)
    required_cols = set()
    optional_cols = set()
    for f in template_version.field_definitions["fields"]:
        if f["required"]:
            required_cols.add(f["label"])
        else:
            optional_cols.add(f["label"])

    results["matched_required_cols"] = required_cols & file_columns
    results["missing_required_cols"] = required_cols - file_columns
    results["matched_optional_cols"] = optional_cols & file_columns
    results["missing_optional_cols"] = optional_cols - file_columns
    for k, v in results.items():
        results[k] = list(v)

    # If the template has required cols, then use this to determine match
    if required_cols:
        results["matches_template"] = (
            len(results["missing_required_cols"]) == 0
        )
    # Template only has optional columns, use this to determine match
    else:
        results["matches_template"] = (
            len(results["missing_optional_cols"]) == 0
        )

    return results
