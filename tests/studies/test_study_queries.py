import pytest
from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.files.models import Version

LAST_ACTIVE_STUDIES = """
query {
    allStudies (orderBy: "-versions__createdAt") {
     edges {
       node {
         id
        kfId
        name
        createdAt
       }
     }
  }
}
"""


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
def test_query_active_studies(db, clients, user_group, allowed):
    """
    Test that ordering the allStudies query by active_at functions as expected.
    """
    client = clients.get(user_group)
    st = StudyFactory()
    st.save
    st2 = StudyFactory()
    st2.save()
    st3 = StudyFactory()
    st3.save()

    for study in (st, st2, st3, st):
        Version(study=study, size=123).save()

    st_id = to_global_id("StudyNode", st.kf_id)
    st2_id = to_global_id("StudyNode", st2.kf_id)

    resp = client.post(
        "/graphql",
        data={"query": LAST_ACTIVE_STUDIES},
        content_type="application/json",
    )
    if allowed:
        edges = resp.json()["data"]["allStudies"]["edges"]
        assert len(edges) == 3
        assert edges[0]["node"]["id"] == st_id
        assert edges[-1]["node"]["id"] == st2_id
