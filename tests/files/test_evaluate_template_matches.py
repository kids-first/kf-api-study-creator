import uuid
from io import BytesIO

import pytest
from django.core.files import File
from graphql_relay import to_global_id, from_global_id

from creator.organizations.factories import OrganizationFactory
from creator.studies.factories import StudyFactory
from creator.files.factories import VersionFactory
from creator.data_templates.factories import TemplateVersionFactory
from creator.files.utils import evaluate_template_match


EVALUTE_TEMPLATE_MATCH = """
mutation ($input: EvaluateTemplateMatchInput!) {
    evaluateTemplateMatch(input: $input) {
      results {
        matchesTemplate
        matchedRequiredCols
        matchedOptionalCols
        missingOptionalCols
        missingRequiredCols
        templateVersion {
          id
          dataTemplate {name}
        }
      }
    }
}
"""


@pytest.fixture
def make_data(permission_client):
    def _make_data(permissions):
        """
        Return helper function to make test data

        Creates 2 template versions and a file version whose columns match
        the first template version's columns
        """
        user, client = permission_client(permissions)
        org = OrganizationFactory()
        study = StudyFactory(organization=org)
        user.organizations.add(org)
        user.studies.add(study)
        user.save()
        fv = VersionFactory()
        fv.root_file.study = study
        fv.root_file.save()
        tvs = TemplateVersionFactory.create_batch(2, studies=[study])
        tv = tvs[0]

        stream = BytesIO()
        tv.template_dataframe.to_csv(stream, sep="\t", index=False)
        stream.seek(0)
        fv.key.save("data.tsv", File(stream))

        return fv, tvs, client
    return _make_data


@pytest.mark.parametrize(
    "permissions,allowed",
    [
        (["view_file", "view_study"], True),
        (["view_my_file", "view_my_study"], True),
        ([], False),
    ],
)
def test_evaluate_match_perms(db, make_data, permissions, allowed):
    """
    Test evaluate_template_match mutation
    """
    fv, tvs, client = make_data(permissions)
    tv = tvs[0]
    variables = {
        "input": {
            "fileVersion": to_global_id("VersionNode", fv.pk),
            "study": to_global_id("StudyNode", fv.root_file.study.pk)
        }
    }
    resp = client.post(
        "/graphql",
        data={"query": EVALUTE_TEMPLATE_MATCH, "variables": variables},
        content_type="application/json",
    )
    fv.refresh_from_db()
    tv.refresh_from_db()

    if allowed:
        results = resp.json()["data"]["evaluateTemplateMatch"]["results"]
        tvs = {t.pk for t in tvs}
        for r in results:
            assert r["matchesTemplate"]
            assert len(r["matchedRequiredCols"]) == 2
            assert not r["matchedOptionalCols"]
            assert not r["missingRequiredCols"]
            assert not r["missingOptionalCols"]
            _, pk = from_global_id(r["templateVersion"]["id"])
            assert pk in tvs
    else:
        assert "Not allowed" in resp.json()["errors"][0]["message"]


def test_evaluate_match_mutation_missing_version(db, permission_client):
    """
    Test evaluate_template_match mutation when file version is missing
    """
    user, client = permission_client([])
    variables = {
        "input": {
            "fileVersion": to_global_id("VersionNode", str(uuid.uuid4())),
            "study": to_global_id("StudyNode", "doesnt matter")
        }
    }
    resp = client.post(
        "/graphql",
        data={"query": EVALUTE_TEMPLATE_MATCH, "variables": variables},
        content_type="application/json",
    )
    assert "does not exist" in resp.json()["errors"][0]["message"]


def test_evaluate_match_missing_study(db, mocker, make_data):
    """
    Test evaluate_template_match mutation when template version is missing
    """
    fv, tvs, client = make_data([])
    variables = {
        "input": {
            "fileVersion": to_global_id("VersionNode", fv.pk),
            "study": to_global_id("StudyNode", str(uuid.uuid4()))
        }
    }
    resp = client.post(
        "/graphql",
        data={"query": EVALUTE_TEMPLATE_MATCH, "variables": variables},
        content_type="application/json",
    )
    assert "does not exist" in resp.json()["errors"][0]["message"]
