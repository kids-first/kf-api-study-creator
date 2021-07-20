import pytest
import uuid
from graphql_relay import to_global_id
from graphql import GraphQLError

from creator.studies.factories import StudyFactory
from creator.organizations.factories import OrganizationFactory
from creator.data_templates.factories import (
    DataTemplateFactory,
    TemplateVersionFactory,
)
from creator.data_templates.mutations.study_templates import check_templates


ADD_TEMPLATES_TO_STUDIES = """
mutation ($input: TemplatesStudiesInput!) {
  addTemplatesToStudies (input: $input) {
    success
    studies {
      id
    }
    templateVersions {
      id
      studies {
        edges {
          node {
            id
          }
        }
      }
    }
  }
}
"""

REMOVE_TEMPLATES_FROM_STUDIES = """
mutation ($input: TemplatesStudiesInput!) {
  removeTemplatesFromStudies (input: $input) {
    success
    studies {
      id
    }
    templateVersions {
      id
      studies {
        edges {
          node {
            id
          }
        }
      }
    }
  }
}
"""


def test_check_templates(db):
    """
    Test helper function used in template version mutations for checking
    template_versions
    """
    # TemplateVersion that doesn't exist should error
    node_ids = [to_global_id("TemplateVersionNode", str(uuid.uuid4()))]
    with pytest.raises(GraphQLError) as e:
        check_templates(node_ids)
    assert "Failed to add/remove" in str(e)


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["change_datatemplate", "change_study"], True),
        (["change_study"], False),
        (["change_datatemplate"], False),
        ([], False),
    ],
)
def test_add_templates_to_studies(db, permission_client, permissions, allowed):
    """
    Test the addTemplatesToStudies mutation in the normal case

    Users without the change_datatemplate permission should not be allowed
    to perform this operation
    """
    # Create a user that is a member of an org and some studies
    user, client = permission_client(permissions)
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org)
    user.studies.set(studies)
    user.organizations.add(org)
    user.save()
    # Create template_versions in organization that user is member of
    dt = DataTemplateFactory(organization=org)
    template_versions = TemplateVersionFactory.create_batch(
        3, data_template=dt
    )
    study_nodes = [to_global_id("StudyNode", s.pk) for s in studies]
    input_ = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t.pk)
            for t in template_versions
        ],
        "studies": study_nodes,
    }
    resp = client.post(
        "/graphql",
        data={
            "query": ADD_TEMPLATES_TO_STUDIES,
            "variables": {"input": input_},
        },
        content_type="application/json",
    )

    if allowed:
        resp_dt = resp.json()["data"]["addTemplatesToStudies"]
        assert resp_dt["templateVersions"] is not None
        assert resp_dt["success"] == True  # noqa
        assert {s["id"] for s in resp_dt["studies"]} == set(study_nodes)
        # Check studies for each template_version
        for template_version in template_versions:
            template_version.refresh_from_db()
            assert template_version.studies.count() == len(studies)
            for study in studies:
                assert template_version.studies.filter(pk=study.pk).exists()

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed."


def test_add_template_does_not_exist(db, permission_client):
    """
    Test the addTemplatesToStudies mutation when one of the template_versions
    does not exist
    """
    user, client = permission_client(["change_datatemplate", "change_study"])
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org)
    user.studies.set(studies)
    user.organizations.add(org)
    user.save()
    # Create template_versions in organization that user is member of
    dt = DataTemplateFactory(organization=org)
    tvs = TemplateVersionFactory.create_batch(3, data_template=dt)
    tv_pks = [t.pk for t in tvs] + [str(uuid.uuid4())]
    input_ = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t) for t in tv_pks
        ],
        "studies": [to_global_id("StudyNode", s.pk) for s in studies],
    }
    resp = client.post(
        "/graphql",
        data={
            "query": ADD_TEMPLATES_TO_STUDIES,
            "variables": {"input": input_},
        },
        content_type="application/json",
    )
    assert "Failed to add/remove" in resp.json()["errors"][0]["message"]


def test_add_templates_not_my_org(db, permission_client):
    """
    Test the addTemplatesToStudies mutation on a template_version for an org
    that the user is not a member of
    """
    user, client = permission_client(["change_datatemplate", "change_study"])
    # Add user to an org
    org1 = OrganizationFactory()
    studies = StudyFactory.create_batch(2, organization=org1)
    user.organizations.add(org1)
    user.studies.set(studies)
    user.save()
    # Create template in diff org
    org2 = OrganizationFactory()
    bad_dt = DataTemplateFactory(organization=org2)
    bad_version = TemplateVersionFactory(data_template=bad_dt)
    template_versions = TemplateVersionFactory.create_batch(
        3, data_template=DataTemplateFactory(organization=org1)
    )
    input_ = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t.pk)
            for t in template_versions + [bad_version]
        ],
        "studies": [to_global_id("StudyNode", s.pk) for s in studies],
    }
    resp = client.post(
        "/graphql",
        data={
            "query": ADD_TEMPLATES_TO_STUDIES,
            "variables": {"input": input_},
        },
        content_type="application/json",
    )

    assert "user's organization." in resp.json()["errors"][0]["message"]


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["change_datatemplate", "change_study"], True),
        (["change_study"], False),
        (["change_datatemplate"], False),
        ([], False),
    ],
)
def test_remove_templates_from_studies(
    db, permission_client, permissions, allowed
):
    """
    Test the removeTemplatesFromStudies mutation in the normal case

    Users without the change_datatemplate permission should not be allowed
    to perform this operation
    """
    # Create a user that is a member of an org and some studies
    user, client = permission_client(permissions)
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(3, organization=org)
    user.studies.set(studies)
    user.organizations.add(org)
    user.save()
    # Create template_versions in organization that user is member of, with
    # 3 studies already assigned
    dt = DataTemplateFactory(organization=org)
    template_versions = TemplateVersionFactory.create_batch(
        3, data_template=dt
    )
    for tv in template_versions:
        tv.studies.add(*studies)
        tv.save()
    study_nodes = [to_global_id("StudyNode", s.pk) for s in studies]
    # Remove 2 of the studies from the template_versions
    input_ = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t.pk)
            for t in template_versions
        ],
        "studies": study_nodes[:-1],
    }
    resp = client.post(
        "/graphql",
        data={
            "query": REMOVE_TEMPLATES_FROM_STUDIES,
            "variables": {"input": input_},
        },
        content_type="application/json",
    )

    if allowed:
        resp_dt = resp.json()["data"]["removeTemplatesFromStudies"]
        assert resp_dt["templateVersions"] is not None
        assert resp_dt["success"] == True  # noqa
        assert {s["id"] for s in resp_dt["studies"]} == set(study_nodes[:-1])
        # Check studies for each template_version
        for template_version in template_versions:
            template_version.refresh_from_db()
            assert template_version.studies.count() == 1
            assert template_version.studies.filter(pk=studies[-1].pk).exists()

    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed."


def test_remove_template_does_not_exist(db, permission_client):
    """
    Test the removeTemplatesFromStudies mutation when one of the
    template_versions does not exist
    """
    user, client = permission_client(["change_datatemplate", "change_study"])
    org = OrganizationFactory()
    studies = StudyFactory.create_batch(3, organization=org)
    user.studies.set(studies)
    user.organizations.add(org)
    user.save()
    # Create template_versions in organization that user is member of, with
    # 3 studies already assigned
    dt = DataTemplateFactory(organization=org)
    tvs = TemplateVersionFactory.create_batch(3, data_template=dt)
    tv_pks = [t.pk for t in tvs] + [str(uuid.uuid4())]
    for tv in tvs:
        tv.studies.add(*studies)
        tv.save()
    study_nodes = [to_global_id("StudyNode", s.pk) for s in studies]
    # Remove 2 of the studies from the template_versions
    input_ = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t) for t in tv_pks
        ],
        "studies": study_nodes[:-1],
    }
    resp = client.post(
        "/graphql",
        data={
            "query": REMOVE_TEMPLATES_FROM_STUDIES,
            "variables": {"input": input_},
        },
        content_type="application/json",
    )
    assert "Failed to add/remove" in resp.json()["errors"][0]["message"]


def test_remove_templates_not_my_org(db, permission_client):
    """
    Test the removeTemplatesFromStudies mutation on a template_version for an
    org that the user is not a member of
    """
    user, client = permission_client(["change_datatemplate", "change_study"])
    # Add user to an org
    org1 = OrganizationFactory()
    studies = StudyFactory.create_batch(3, organization=org1)
    user.organizations.add(org1)
    user.studies.set(studies)
    user.save()

    # Create template in diff org
    org2 = OrganizationFactory()
    bad_dt = DataTemplateFactory(organization=org2)
    bad_version = TemplateVersionFactory(data_template=bad_dt)
    tvs = TemplateVersionFactory.create_batch(
        3, data_template=DataTemplateFactory(organization=org1)
    )
    tvs.append(bad_version)
    for tv in tvs:
        tv.studies.add(*studies)
        tv.save()
    study_nodes = [to_global_id("StudyNode", s.pk) for s in studies]
    input_ = {
        "templateVersions": [
            to_global_id("TemplateVersionNode", t.pk) for t in tvs
        ],
        "studies": study_nodes[:-1],
    }
    resp = client.post(
        "/graphql",
        data={
            "query": REMOVE_TEMPLATES_FROM_STUDIES,
            "variables": {"input": input_},
        },
        content_type="application/json",
    )

    assert "user's organization." in resp.json()["errors"][0]["message"]
