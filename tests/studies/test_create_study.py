import pytest
from datetime import datetime
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.tasks import setup_cavatica_task
from creator.files.models import Study
from creator.studies.factories import StudyFactory
from creator.users.factories import UserFactory
from creator.organizations.factories import OrganizationFactory
from creator.projects.models import Project
from creator.projects.cavatica import attach_volume

User = get_user_model()


CREATE_STUDY_MUTATION = """
mutation newStudy($input: CreateStudyInput!, $workflows: [String]) {
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
            shortCode
            domain
            program
            collaborators { edges { node { id username } } }
        }
    }
}
"""


@pytest.fixture
def mock_cavatica(mocker, settings):
    """ Mocks out project setup functions """
    settings.CAVATICA_HARMONIZATION_TOKEN = "testtoken"
    settings.CAVATICA_DELIVERY_TOKEN = "testtoken"
    cavatica = mocker.patch("creator.studies.schema.django_rq.enqueue")
    return cavatica


@pytest.fixture
def mock_post(mocker):
    """ Creates a mock response for the dataservice """
    post = mocker.patch("requests.post")

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
                    "foobar": "baz",
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
                    "short_code": "HELLO",
                    "domain": "CANCER",
                    "program": "CHOP",
                },
            }

    post.return_value = MockResp()
    return post


@pytest.fixture
def mock_error(mocker):
    """ Mock a failed response from the dataservice """
    post = mocker.patch("requests.post")

    class MockResp:
        def __init__(self):
            self.status_code = 400

        def json(self):
            return {"message": "error"}

    post.return_value = MockResp()
    return post


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", False),
        ("Investigators", False),
        ("Bioinformatics", False),
        (None, False),
    ],
)
def test_create_study_mutation(
    db, clients, mock_post, mock_cavatica, user_group, allowed
):
    """
    Only admins should be allowed to create studies
    """
    collaborator = UserFactory()
    user = User.objects.filter(groups__name=user_group).first()
    organization = OrganizationFactory(members=[user] if user else [])
    client = clients.get(user_group)
    variables = {
        "input": {
            "externalId": "Test Study",
            "collaborators": [to_global_id("UserNode", collaborator.id)],
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    if allowed:
        resp_body = resp.json()["data"]["createStudy"]["study"]
        assert resp_body["externalId"] == "Test Study"
        assert resp_body["shortCode"] == "HELLO"
        assert resp_body["domain"] == "CANCER"
        assert resp_body["program"] == "CHOP"
        assert Study.objects.count() == 1
        assert Study.objects.first().external_id == "Test Study"
        assert Study.objects.first().short_code == "HELLO"
        assert mock_cavatica.call_count == 1
        assert Study.objects.first().collaborators.count() == 1
    else:
        assert "errors" in resp.json()
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        assert Study.objects.count() == 0
        assert mock_cavatica.call_count == 0


def test_create_study_collaborator_does_not_exist(
    db, clients, mock_post, mock_cavatica
):
    """
    Study should not be created and an error returned if one of the
    collaborators does not exist
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")
    variables = {
        "input": {
            "externalId": "Test Study",
            "collaborators": [to_global_id("UserNode", 123)],
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "does not exist" in resp.json()["errors"][0]["message"]
    assert Study.objects.count() == 0
    assert mock_cavatica.call_count == 0


def test_create_study_organization_does_not_exist(db, clients, mock_post):
    """
    Test that a study may not be created if the specified organization does not
    exist.
    """
    client = clients.get("Administrators")

    variables = {
        "input": {
            "externalId": "Test Study",
            "collaborators": [to_global_id("UserNode", 123)],
            "organization": to_global_id("OrganizationNode", "ABC"),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert (
        "Organization ABC does not exist"
        in resp.json()["errors"][0]["message"]
    )
    assert Study.objects.count() == 0


def test_dataservice_call(db, clients, mock_post, settings):
    """
    Test that the dataservice is called correctly
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")
    variables = {
        "input": {
            "externalId": "Test Study",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_post.call_count == 1
    mock_post.assert_called_with(
        f"{settings.DATASERVICE_URL}/studies",
        json={
            "external_id": "Test Study",
            "short_code": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        },
        headers=settings.REQUESTS_HEADERS,
        timeout=settings.REQUESTS_TIMEOUT,
    )
    assert Study.objects.count() == 1


def test_dataservice_feat_flag(db, clients, mock_post, settings):
    """
    Test that creating studies does not work when the feature flag is turned
    off.
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")

    settings.FEAT_DATASERVICE_CREATE_STUDIES = False

    variables = {
        "input": {
            "externalId": "Test Study",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_post.call_count == 0
    assert Study.objects.count() == 0
    resp_message = resp.json()["errors"][0]["message"]
    assert resp_message.startswith("Creating studies is not enabled")


def test_dataservice_error(db, clients, mock_error):
    """
    Test behavior when dataservice returns an error.
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")
    variables = {
        "input": {
            "externalId": "Test Study",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_error.call_count == 1
    assert Study.objects.count() == 0
    resp_message = resp.json()["errors"][0]["message"]
    assert resp_message.startswith("Problem creating study:")


def test_study_buckets_settings(db, clients, mock_post, settings, mocker):
    """
    Test that buckets are only created if the correct settings are configured
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")
    settings.FEAT_STUDY_BUCKETS_CREATE_BUCKETS = True
    settings.STUDY_BUCKETS_REGION = "us-east-1"
    settings.STUDY_BUCKETS_LOGGING_BUCKET = "bucket"
    settings.STUDY_BUCKETS_DR_LOGGING_BUCKET = "logging-bucket"
    settings.STUDY_BUCKETS_REPLICATION_ROLE = "arn:::"
    settings.STUDY_BUCKETS_INVENTORY_LOCATION = "bucket-metrics/inventory"

    mock_setup = mocker.patch("creator.studies.schema.django_rq.enqueue")

    variables = {
        "input": {
            "externalId": "Test Study",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert mock_setup.call_count == 1

    settings.STUDY_BUCKETS_REGION = None

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    # Setup should not have been called
    assert mock_setup.call_count == 1


def test_workflows(db, settings, mocker, clients, mock_post):
    """
    Test that a new study may be created with specific workflows
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")
    settings.CAVATICA_HARMONIZATION_TOKEN = "testtoken"
    settings.CAVATICA_DELIVERY_TOKEN = "testtoken"
    setup_cavatica = mocker.patch("creator.studies.schema.django_rq.enqueue")

    variables = {
        "workflows": ["bwa_mem"],
        "input": {
            "externalId": "Test Study",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        },
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert setup_cavatica.call_count == 1
    setup_cavatica.assert_called_with(
        setup_cavatica_task,
        Study.objects.first().kf_id,
        ["bwa_mem"],
        User.objects.filter(groups__name="Administrators").first().sub,
        depends_on=None,
    )

    # Try multiple workflows
    setup_cavatica.reset_mock()
    workflows = ["bwa_mem", "mutect2_somatic_mode", "kallisto"]
    variables = {
        "workflows": workflows,
        "input": {
            "externalId": "Test Study",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HOWDY",
            "domain": "CANCER",
            "program": "CHOP",
        },
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert setup_cavatica.call_count == 1
    setup_cavatica.assert_called_with(
        setup_cavatica_task,
        Study.objects.first().kf_id,
        workflows,
        User.objects.filter(groups__name="Administrators").first().sub,
        depends_on=None,
    )


@pytest.mark.parametrize(
    "field",
    [
        "name",
        "visible",
        "attribution",
        "dataAccessAuthority",
        "releaseStatus",
        "shortName",
        "version",
        "description",
        "awardeeOrganization",
    ],
)
def test_text_fields(db, clients, settings, mock_post, field):
    """
    Test text inputs for different fields
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")

    settings.FEAT_CAVATICA_CREATE_PROJECTS = False

    variables = {
        "input": {
            "externalId": "TEST",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    variables["input"][field] = "Lorem Ipsum"
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" not in resp.json()


@pytest.mark.parametrize("field", ["anticipatedSamples"])
def test_integer_fields(db, clients, settings, mock_post, field):
    """
    Test positive integer inputs for different fields
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")

    settings.FEAT_CAVATICA_CREATE_PROJECTS = False

    variables = {
        "input": {
            "externalId": "TEST",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    variables["input"][field] = 324
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" not in resp.json()


@pytest.mark.parametrize("field", ["description", "awardeeOrganization"])
def test_internal_fields(db, clients, settings, mock_post, field):
    """
    Test that inputs for our internal study fields are saved correctly.

    TODO: Merge with test_text_fields by making dataservice mock more flexible
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")

    settings.FEAT_CAVATICA_CREATE_PROJECTS = False

    variables = {
        "input": {
            "externalId": "TEST",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    variables["input"][field] = "Lorem Ipsum"
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )
    assert "errors" not in resp.json()
    assert resp.json()["data"]["createStudy"]["study"][field] == "Lorem Ipsum"


@pytest.mark.parametrize("field", ["releaseDate"])
def test_internal_datetime_fields(db, clients, settings, mock_post, field):
    """
    Test that inputs datetime study fields are saved correctly.
    """
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")

    settings.FEAT_CAVATICA_CREATE_PROJECTS = False

    variables = {
        "input": {
            "externalId": "TEST",
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    d = datetime.now()
    variables["input"][field] = d.strftime("%Y-%m-%d")
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )
    assert "errors" not in resp.json()
    assert resp.json()["data"]["createStudy"]["study"][field] == str(
        d.strftime("%Y-%m-%d")
    )


def test_attach_volumes(db, clients, settings, mock_cavatica_api):
    """ Test that volumes are attached for new studies """
    client = clients.get("Administrators")

    settings.FEAT_CAVATICA_MOUNT_VOLUMES = True
    settings.CAVATICA_HARMONIZATION_TOKEN = "abc"
    settings.CAVATICA_READWRITE_ACCESS_KEY = "abc"
    settings.CAVATICA_READWRITE_SECRET_KEY = "123"
    settings.CAVATICA_DELIVERY_ACCOUNT = "kids-first"

    study = StudyFactory(kf_id="SD_00000000", name="test", bucket="my bucket")
    study.save()

    attach_volume(study)

    mock_cavatica_api.Api().volumes.create_s3_volume.assert_called_with(
        name=study.kf_id,
        description="Created by the Study Creator for 'test'",
        bucket=study.bucket,
        access_key_id="abc",
        secret_access_key="123",
        access_mode="RW",
    )


def test_short_code_unique(db, clients, mock_post, mock_cavatica):
    """
    Check the uniqueness constraint of the short_code attr during Study
    creation.
    """
    collaborator = UserFactory()
    user = User.objects.filter(groups__name="Administrators").first()
    organization = OrganizationFactory(members=[user])
    client = clients.get("Administrators")
    variables = {
        "input": {
            "externalId": "Test Study",
            "collaborators": [to_global_id("UserNode", collaborator.id)],
            "organization": to_global_id("OrganizationNode", organization.pk),
            "shortCode": "HELLO",
            "domain": "CANCER",
            "program": "CHOP",
        }
    }
    _ = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )
    assert Study.objects.count() == 1
    assert mock_cavatica.call_count == 1

    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": CREATE_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert resp.json()["errors"][0]["message"] == (
        "Study short_code provided was not unique."
    )
    assert Study.objects.count() == 1
    assert mock_cavatica.call_count == 1
