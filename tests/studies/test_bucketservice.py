import pytest
from hypothesis import given, settings
from hypothesis.strategies import text, integers, characters, dates
from django.contrib.auth import get_user_model

from creator.files.models import Study
from creator.studies.factories import StudyFactory
from creator.studies.bucketservice import setup_bucket
from creator.tasks import setup_bucket_task


User = get_user_model()


CREATE_STUDY_MUTATION = """
mutation newStudy($input: StudyInput!, $workflows: [String]) {
    createStudy(input: $input, workflows: $workflows) {
        study {
            kfId
            externalId
            name
            description
            visible
            attribution
            dataAccessAuthority
            releaseStatus
            shortName
            version
            anticipatedSamples
            awardeeOrganization
            releaseDate
        }
    }
}
"""


@pytest.fixture
def mock_dataservice_post(mocker):
    """ Creates a mock response for the dataservice """
    post = mocker.patch("creator.studies.schema.requests.post")

    class MockResp:
        def __init__(self):
            self.status_code = 201

        def json(self):
            return {
                "_links": {
                    "collection": "/studies",
                    "investigator": None,
                    "participants": "/participants?study_id=SD_6HET65MK",
                    "self": "/studies/SD_6HET65MK",
                    "study_files": "/study-files?study_id=SD_6HET65MK",
                },
                "_status": {
                    "code": 201,
                    "message": "study SD_6HET65MK created",
                },
                "results": {
                    "attribution": None,
                    "created_at": "2019-08-05T17:50:21.681779+00:00",
                    "data_access_authority": "dbGaP",
                    "external_id": "Test Study",
                    "kf_id": "SD_6HET65MK",
                    "modified_at": "2019-08-05T17:50:21.681802+00:00",
                    "name": "testing",
                    "release_status": None,
                    "short_name": None,
                    "version": None,
                    "visible": True,
                },
            }

    post.return_value = MockResp()
    return post


@pytest.fixture
def mock_bucketservice_post(mocker):
    """ Creates a mock response for the bucketservice """
    post = mocker.patch("creator.studies.bucketservice.requests.post")

    class MockResp:
        def __init__(self):
            self.status_code = 201

        def json(self):
            return {"bucket": "my-bucket/sd-6het65mk"}

        def raise_for_status(self):
            pass

    post.return_value = MockResp()
    return post


def test_bucket_creation(
    db, admin_client, mocker, settings, mock_dataservice_post
):
    """
    Test that the bucket setup is invoked on study creation
    """
    settings.FEAT_BUCKETSERVICE_CREATE_BUCKETS = True
    settings.BUCKETSERVICE_URL = "http://bucketservice"

    mock_setup = mocker.patch("creator.studies.schema.django_rq.enqueue")

    variables = {"input": {"externalId": "Test Study"}}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_setup.call_count == 1
    mock_setup.assert_called_with(
        setup_bucket_task, Study.objects.first().kf_id
    )


def test_bucket_setup(
    db, admin_client, mocker, settings, mock_bucketservice_post
):
    """
    Test that the bucketservice is invoked correctly
    """
    # Needed to allow caching of mocks
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    }

    mock_token = mocker.patch(
        "creator.studies.bucketservice.get_service_token"
    )
    mock_token.return_values = "ABC"
    study = StudyFactory(kf_id="SD_00000000", bucket="")
    assert study.bucket == ""
    setup_bucket(study)

    assert study.bucket == "my-bucket/sd-6het65mk"
    assert mock_bucketservice_post.call_count == 1
    args, kwargs = mock_bucketservice_post.call_args_list[0]
    assert args[0] == settings.BUCKETSERVICE_URL + "/buckets"
    assert kwargs["timeout"] == 30
    assert kwargs["json"] == {"study_id": "SD_00000000"}
