import pytest
import uuid
from datetime import datetime
from graphql_relay import to_global_id
from django.contrib.auth import get_user_model

from creator.studies.factories import StudyFactory
from creator.organizations.factories import OrganizationFactory

User = get_user_model()


TRANSFER_STUDY_MUTATION = """
mutation TransferStudy($study: ID!, $organization: ID!) {
  transferStudy(study:$study, organization:$organization) {
    study {
      id
      name
      organization {
        id
        name
      }
    }
  }
}
"""


def test_transfer_study_mutation(db, permission_client):
    """
    Only users with the change_organization permission may transfer study.
    """
    user, client = permission_client(["change_organization"])
    source_org = OrganizationFactory(members=[user])
    destination_org = OrganizationFactory(members=[user])
    study = StudyFactory()
    study.organization = source_org
    study.save()

    variables = {
        "organization": to_global_id("OrganizationNode", destination_org.id),
        "study": to_global_id("StudyNode", study.kf_id)
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": TRANSFER_STUDY_MUTATION, "variables": variables},
    )

    resp_data = resp.json()["data"]["transferStudy"]["study"]
    assert resp_data["organization"]['name'] == destination_org.name


def test_transfer_study_mutation_not_source(db, permission_client):
    """
    Users who is not the member of the source organization is
    not allowed to transfer study
    """
    user, client = permission_client(["change_organization"])
    member_org = OrganizationFactory(members=[user])
    no_member_org = OrganizationFactory()
    study = StudyFactory()
    study.organization = no_member_org
    study.save()

    variables = {
        "organization": to_global_id("OrganizationNode", member_org.id),
        "study": to_global_id("StudyNode", study.kf_id)
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={
            "query": TRANSFER_STUDY_MUTATION,
            "variables": variables
        },
    )

    message = resp.json()["errors"][0]["message"]
    assert "only transfer study from an organization" in message


def test_transfer_study_mutation_not_destination(db, permission_client):
    """
    Users who is not the member of the destination organization is
    not allowed to transfer study
    """
    user, client = permission_client(["change_organization"])
    member_org = OrganizationFactory(members=[user])
    no_member_org = OrganizationFactory()
    study = StudyFactory()
    study.organization = member_org
    study.save()

    variables = {
        "organization": to_global_id("OrganizationNode", no_member_org.id),
        "study": to_global_id("StudyNode", study.kf_id)
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={
            "query": TRANSFER_STUDY_MUTATION,
            "variables": variables
        },
    )

    message = resp.json()["errors"][0]["message"]
    assert "only transfer study to an organization" in message


def test_organization_not_found(db, permission_client):
    """
    Test behavior when the specified organization does not exist
    """
    user, client = permission_client(["change_organization"])
    source_org = OrganizationFactory(members=[user])
    study = StudyFactory()
    study.organization = source_org
    study.save()

    variables = {
        "organization": to_global_id("OrganizationNode", uuid.uuid4()),
        "study": to_global_id("StudyNode", study.kf_id)
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": TRANSFER_STUDY_MUTATION, "variables": variables},
    )

    message = resp.json()["errors"][0]["message"]
    assert "does not exist" in message


def test_study_not_found(db, permission_client):
    """
    Test behavior when the specified study does not exist
    """
    user, client = permission_client(["change_organization"])
    source_org = OrganizationFactory(members=[user])
    destination_org = OrganizationFactory(members=[user])

    variables = {
        "organization": to_global_id("OrganizationNode", source_org.id),
        "study": to_global_id("StudyNode", 123)
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": TRANSFER_STUDY_MUTATION, "variables": variables},
    )

    assert "errors" in resp.json()
    assert "123 does not exist" in resp.json()["errors"][0]["message"]
