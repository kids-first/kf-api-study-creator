import pytest
from graphql_relay import to_global_id
from graphql import GraphQLError
from django.contrib.auth import get_user_model

from creator.studies.models import Membership
from creator.studies.models import Study
from creator.files.models import File
from creator.data_reviews.models import DataReview, State
from creator.data_reviews.factories import DataReviewFactory
from creator.data_reviews.mutations import check_review_files

User = get_user_model()

CREATE_DATA_REVIEW = """
mutation ($input: CreateDataReviewInput!) {
    createDataReview(input: $input) {
        dataReview {
            id
            kfId
            createdAt
            name
            description
            state
            study { id kfId }
            versions { edges { node { id kfId } } }
        }
    }
}
"""

UPDATE_DATA_REVIEW = """
mutation ($id: ID!, $input: UpdateDataReviewInput!) {
    updateDataReview(id: $id, input: $input) {
        dataReview {
            id
            kfId
            createdAt
            name
            description
            state
            study { id kfId }
            versions { edges { node { id kfId } } }
        }
    }
}
"""

AWAIT_DATA_REVIEW = """
mutation ($id: ID!) {
    awaitDataReview(id: $id) {
        dataReview {
            id
            kfId
            state
        }
    }
}

"""
APPROVE_DATA_REVIEW = """
mutation ($id: ID!) {
    approveDataReview(id: $id) {
        dataReview {
            id
            kfId
            state
        }
    }
}
"""

CLOSE_DATA_REVIEW = """
mutation ($id: ID!) {
    closeDataReview(id: $id) {
        dataReview {
            id
            kfId
            state
        }
    }
}
"""

REOPEN_DATA_REVIEW = """
mutation ($id: ID!) {
    reopenDataReview(id: $id) {
        dataReview {
            id
            kfId
            state
        }
    }
}
"""


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
@pytest.mark.parametrize(
    "end_state,expected_error",
    [
        (State.NOT_STARTED, None),
        (State.IN_REVIEW, None),
    ],
)
def test_create_data_review(
    db, clients, prep_file, end_state, expected_error, user_group, allowed
):
    """
    Test the create mutation.

    1) Create a review with no files. State should be State.NOT_STARTED
    2) Create a review with files. State should be State.IN_REVIEW
    """
    client = clients.get(user_group)
    simple_update = False
    if end_state == State.NOT_STARTED:
        simple_update = True

    # Create a study with some files
    study_file_versions = []
    for i in range(2):
        study_id, file_id, _ = prep_file(authed=True)
        study_file_versions.append(
            to_global_id(
                "VersionNode", File.objects.get(pk=file_id).versions.first().pk
            )
        )
    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(
            collaborator=user, study=Study.objects.get(pk=study_id)
        ).save()

    # Send request
    input_ = {
        "name": "A Data Review",
        "description": "A description",
        "study": to_global_id("StudyNode", study_id),
    }
    if not simple_update:
        input_["versions"] = study_file_versions
    resp = client.post(
        "/graphql",
        data={"query": CREATE_DATA_REVIEW, "variables": {"input": input_}},
        content_type="application/json",
    )

    if allowed:
        # Check values
        dr = resp.json()["data"]["createDataReview"]["dataReview"]
        assert dr is not None
        for k, v in input_.items():
            assert v is not None

        # Check proper state was set and correct task queued
        data_review = DataReview.objects.get(pk=dr["kfId"])
        assert data_review.state == end_state
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
@pytest.mark.parametrize(
    "start_state,end_state,expected_error",
    [
        (State.NOT_STARTED, State.IN_REVIEW, None),
        (State.NOT_STARTED, State.NOT_STARTED, None),
        (State.WAITING, State.IN_REVIEW, None),
        (State.CLOSED, State.CLOSED, "Cannot modify"),
        (State.COMPLETED, State.COMPLETED, "Cannot modify"),
    ],
)
def test_update_data_review(
    db,
    clients,
    prep_file,
    start_state,
    end_state,
    expected_error,
    user_group,
    allowed,
):
    """
    Test the update mutation with multiple updates:

    0) Update name, description to a review not started
    1) Add new file to a review that hasn't been started
    2) Add new file to review in waiting for updates state

    Both 1,2, ^ should result in state = State.IN_REVIEW

    3) Try to modify a closed review
    4) Try to modify a complete review

    Both 3,4 ^ should result in error
    """
    client = clients.get(user_group)
    simple_update = False
    if start_state == end_state and (start_state == State.NOT_STARTED):
        simple_update = True

    # Create a study with some files
    study_file_versions = []
    for i in range(2):
        study_id, file_id, _ = prep_file(authed=True)
        study_file_versions.append(
            to_global_id(
                "VersionNode", File.objects.get(pk=file_id).versions.first().pk
            )
        )

    # Create data review with no files
    data_review = DataReviewFactory(
        study=Study.objects.get(pk=study_id), state=start_state
    )
    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=data_review.study).save()

    # Send request
    input_ = {
        "name": "foobar",
        "description": "foobar",
    }
    if not simple_update:
        input_["versions"] = study_file_versions

    resp = client.post(
        "/graphql",
        data={
            "query": UPDATE_DATA_REVIEW,
            "variables": {
                "id": to_global_id("DataReviewNode", data_review.pk),
                "input": input_,
            },
        },
        content_type="application/json",
    )

    # Check permissions
    if not allowed:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        return

    # Check expected end_state
    data_review.refresh_from_db()
    assert data_review.state == end_state

    # Error
    if expected_error:
        assert expected_error in resp.json()["errors"][0]["message"]
    # Success
    else:
        dr = resp.json()["data"]["updateDataReview"]["dataReview"]
        assert dr is not None
        for k, v in input_.items():
            assert v is not None


@pytest.mark.parametrize(
    "user_group,allowed",
    [
        ("Administrators", True),
        ("Services", False),
        ("Developers", True),
        ("Investigators", True),
        ("Bioinformatics", True),
        (None, False),
    ],
)
@pytest.mark.parametrize(
    "start_state,end_state,mutation,expected_error",
    [
        (State.IN_REVIEW, State.WAITING, AWAIT_DATA_REVIEW, None),
        (State.IN_REVIEW, State.COMPLETED, APPROVE_DATA_REVIEW, None),
        (State.IN_REVIEW, State.CLOSED, CLOSE_DATA_REVIEW, None),
        (State.CLOSED, State.IN_REVIEW, REOPEN_DATA_REVIEW, None),
        (
            State.NOT_STARTED,
            State.NOT_STARTED,
            APPROVE_DATA_REVIEW,
            "when data review is in state",
        ),
    ],
)
def test_review_actions(
    db,
    clients,
    start_state,
    end_state,
    mutation,
    expected_error,
    user_group,
    allowed,
):
    client = clients.get(user_group)

    # Create data review with no files
    data_review = DataReviewFactory(state=start_state)
    if user_group:
        user = User.objects.filter(groups__name=user_group).first()
        Membership(collaborator=user, study=data_review.study).save()

    # Send request
    resp = client.post(
        "/graphql",
        data={
            "query": mutation,
            "variables": {
                "id": to_global_id("DataReviewNode", data_review.pk),
            },
        },
        content_type="application/json",
    )

    # Check permissions
    if not allowed:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
        return

    # Check expected end_state
    data_review.refresh_from_db()
    assert data_review.state == end_state

    # Error
    if expected_error:
        assert expected_error in resp.json()["errors"][0]["message"]
    # Success
    else:
        for k in resp.json()["data"]:
            mutation_name = k
        dr = resp.json()["data"][mutation_name]["dataReview"]
        assert dr is not None


def test_update_review_bad_file(db, clients, prep_file):
    """
    Test check_review_file method with valid / invalid file versions
    """
    # Valid case - New data review with files from same study
    study_id, file_id, _ = prep_file(authed=True)
    dr = DataReviewFactory(study=Study.objects.get(pk=study_id))
    version = File.objects.get(pk=file_id).versions.first()
    review_file_ids = check_review_files(
        {"versions": [to_global_id("VersionNode", version.pk)]}, dr
    )
    assert len(review_file_ids) == 1
    dr.versions.set(review_file_ids)
    dr.save()

    # Invalid case - data review with files from different study
    study_id, file_id, _ = prep_file(authed=False)
    version = File.objects.get(pk=file_id).versions.first()
    with pytest.raises(GraphQLError) as e:
        review_file_ids = check_review_files(
            {"versions": [to_global_id("VersionNode", version.pk)]}, dr
        )
    assert "Error in modifying data_review" in str(e)


def test_update_review_files_changed(db, clients, prep_file):
    """
    Test check_review_file method with review file version changes
    """
    # Add files to data review w no files
    study_id, file_id, _ = prep_file(authed=True)
    dr = DataReviewFactory(study=Study.objects.get(pk=study_id))
    version1_id = to_global_id(
        "VersionNode", File.objects.get(pk=file_id).versions.first().pk
    )
    review_file_ids = check_review_files({"versions": [version1_id]}, dr)
    assert len(review_file_ids) == 1
    dr.versions.set(review_file_ids)
    dr.save()

    # Add same file to data review
    review_file_ids = check_review_files({"versions": [version1_id]}, dr)
    assert review_file_ids is None

    # Add new files to data review with files
    vids = []
    for i in range(2):
        study_id, file_id, _ = prep_file(authed=True)
        vids.append(
            to_global_id(
                "VersionNode", File.objects.get(pk=file_id).versions.first().pk
            )
        )
    review_file_ids = check_review_files({"versions": vids}, dr)
    assert len(review_file_ids) == 2
    dr.versions.set(review_file_ids)
    dr.save()

    # Delete all files from data review
    review_file_ids = check_review_files({"versions": []}, dr)
    assert len(review_file_ids) == 0
    dr.versions.set(review_file_ids)
    dr.save()

    # Delete all files from data review w no files
    review_file_ids = check_review_files({"versions": []}, dr)
    assert review_file_ids is None
