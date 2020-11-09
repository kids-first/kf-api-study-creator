from pprint import pprint
import pytest
from graphql_relay import to_global_id

INGEST_RUN = """
query ($id: ID!) {
    ingestRun(id: $id) {
        id
        name
        inputHash
        versions {
          edges {
            node {
              kfId
            }
          }
        }
    }
}
"""

ALL_INGEST_RUNS = """
query {
    allIngestRuns {
     edges {
       node {
         id
         name
         inputHash
         versions {
           edges {
             node {
               kfId
             }
           }
         }
       }
     }
  }
}
"""

FILTER_ALL_INGEST_RUNS = """
query ($name: String!){
    allIngestRuns(name_Icontains: $name) {
     edges {
       node {
         id
         name
         versions {
           edges {
             node {
               kfId
             }
           }
         }
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
def test_query_ingest_run(db, clients, ingest_runs, user_group, allowed):
    client = clients.get(user_group)

    ingest_run = ingest_runs(n=1)[0]

    variables = {"id": to_global_id("IngestRunNode", ingest_run.id)}

    resp = client.post(
        "/graphql",
        data={"query": INGEST_RUN, "variables": variables},
        content_type="application/json",
    )

    if allowed:
        node = resp.json()["data"]["ingestRun"]
        assert node["id"] == to_global_id("IngestRunNode", ingest_run.id)
        assert node["name"]
        assert node["versions"]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


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
def test_query_all_ingest_runs(db, clients, ingest_runs, user_group, allowed):
    client = clients.get(user_group)

    # Create an ingest run for each file
    n = 2
    ingest_runs(n=n)

    resp = client.post(
        "/graphql",
        data={"query": ALL_INGEST_RUNS},
        content_type="application/json",
    )

    if allowed:
        pprint(resp.json())
        edges = resp.json()["data"]["allIngestRuns"]["edges"]
        assert len(edges) == n
        for edge in edges:
            assert "id" in edge["node"]
            assert "name" in edge["node"]
            assert "versions" in edge["node"]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"


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
def test_filter_query_all_ingest_runs(
    db, clients, ingest_runs, user_group, allowed
):
    client = clients.get(user_group)

    # Create an ingest run for each file
    ingest_runs = ingest_runs(n=2)
    version_id_filter = ingest_runs[0].versions.first().kf_id

    resp = client.post(
        "/graphql",
        data={
            "query": FILTER_ALL_INGEST_RUNS,
            "variables": {"name": version_id_filter},
        },
        content_type="application/json",
    )

    if allowed:
        edges = resp.json()["data"]["allIngestRuns"]["edges"]
        assert len(edges) == 1
        assert version_id_filter in edges[0]["node"]["name"]
    else:
        assert resp.json()["errors"][0]["message"] == "Not allowed"
