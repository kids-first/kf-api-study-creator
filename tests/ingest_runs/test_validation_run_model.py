import pytest

from django.contrib.auth import get_user_model

from creator.ingest_runs.models import (
    ValidationRun,
    ValidationResultset,
)
from creator.data_reviews.factories import DataReviewFactory, DataReview
from django.core.exceptions import ValidationError
from creator.studies.models import Study
from creator.files.models import File

User = get_user_model()


@pytest.fixture
def data_review(db, clients, prep_file):
    """
    Create a data review with two file versions
    """
    versions = []
    for i in range(2):
        study_id, file_id, _ = prep_file(authed=True)
        versions.append(File.objects.get(pk=file_id).versions.first())
    dr = DataReviewFactory(
        creator=User.objects.first(),
        study=Study.objects.get(pk=study_id),
        versions=versions
    )
    dr.save()
    dr.refresh_from_db()
    return dr


def test_validation_run(data_review):
    """
    Test ValidationRun model
    """
    # Create a good validation run for the review
    vr = ValidationRun(data_review=data_review)
    vr.clean()
    vr.save()
    # Check that study, versions, and input_hash got set right
    versions = [v.pk for v in vr.versions.all()]
    assert set(versions) == set([v.pk for v in data_review.versions.all()])
    assert vr.input_hash
    assert vr.study == data_review.study


def test_validation_resultset(data_review):
    """
    Test ValidationResultset model
    """
    vr = ValidationResultset(data_review=data_review)
    vr.clean()
    vr.save()
    assert vr.study == data_review.study
    assert vr.data_review.pk in vr.report_path
    assert vr.data_review.pk in vr.results_path


def test_missing_study():
    """
    Test missing study on ValidationRun and ValidationResultset
    """
    # No data review no study
    objs = [ValidationRun(), ValidationResultset()]
    for obj in objs:
        with pytest.raises(ValidationError) as e:
            obj.clean()
            assert "must have an associated DataReview" in str(e)

    # Has data review with no study
    for obj in objs:
        obj.data_review = DataReview()
        with pytest.raises(ValidationError) as e:
            obj.clean()
            assert "must have an associated DataReview" in str(e)
