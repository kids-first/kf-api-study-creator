import pytest

from graphql_relay import to_global_id

from creator.studies.factories import StudyFactory
from creator.releases.factories import ReleaseFactory
from creator.files.factories import FileFactory
from creator.users.factories import UserFactory


# This is a real query from production run to fetch data for a study

STUDY_QUERY = """
query Study($id: ID!) {
  study(id: $id) {
    ...StudyBasicFields
    ...StudyInfoFields
    collaborators {
      edges {
        joinedOn
        node {
          ...UserFields
          ...GroupFields
          __typename
        }
        __typename
      }
      __typename
    }
    events(first: 10, orderBy: "-created_at") {
      edges {
        node {
          ...EventFields
          __typename
        }
        __typename
      }
      __typename
    }
    projects {
      edges {
        node {
          ...ProjectFields
          study {
            ...StudyBasicFields
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    files {
      edges {
        node {
          ...FileFields
          versions {
            edges {
              node {
                id
                kfId
                size
                createdAt
                state
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment StudyBasicFields on StudyNode {
  id
  name
  shortName
  kfId
  investigatorName
  createdAt
  modifiedAt
  __typename
}

fragment StudyInfoFields on StudyNode {
  bucket
  attribution
  dataAccessAuthority
  externalId
  releaseStatus
  version
  releaseDate
  description
  anticipatedSamples
  awardeeOrganization
  sequencingStatus
  ingestionStatus
  phenotypeStatus
  slackNotify
  slackChannel
  __typename
}

fragment FileFields on FileNode {
  id
  kfId
  name
  description
  fileType
  downloadUrl
  tags
  validTypes
  __typename
}

fragment EventFields on EventNode {
  id
  uuid
  createdAt
  eventType
  description
  __typename
}

fragment ProjectFields on ProjectNode {
  id
  createdBy
  createdOn
  description
  modifiedOn
  name
  projectId
  projectType
  url
  workflowType
  deleted
  __typename
}

fragment UserFields on UserNode {
  id
  displayName
  dateJoined
  username
  email
  picture
  __typename
}

fragment GroupFields on UserNode {
  groups {
    edges {
      node {
        id
        name
        permissions {
          edges {
            node {
              id
              name
              codename
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
  __typename
}
"""

ALL_STUDIES_QUERY = """
query AllStudies {
  allStudies {
    edges {
      node {
        ...StudyBasicFields
        investigatorName
        bucket
        externalId
        version
        anticipatedSamples
        slackChannel
        sequencingStatus
        ingestionStatus
        phenotypeStatus
        releases(first: 1, orderBy: \"-created_at\", state: \"published\") {
          edges {
            node {
              id
              kfId
              name
              version
              createdAt
              creator {
                ...UserFields
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        collaborators {
          edges {
            node {
              ...UserFields
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment StudyBasicFields on StudyNode {
  id
  name
  shortName
  kfId
  investigatorName
  createdAt
  modifiedAt
  __typename
}

fragment UserFields on UserNode {
  id
  displayName
  dateJoined
  username
  email
  picture
  __typename
}
"""


def test_all_studies_query(db, django_assert_num_queries, clients):
    """
    Benchmark to ensure that we are optimizing our study query correctly.
    """
    client = clients.get("Administrators")

    users = UserFactory.create_batch(10)
    studies = StudyFactory.create_batch(10)
    releases = ReleaseFactory.create_batch(10)

    studies[0].collaborators.set(users)
    studies[0].save()

    with django_assert_num_queries(34) as queries:

        resp = client.post(
            "/graphql",
            content_type="application/json",
            data={"query": ALL_STUDIES_QUERY},
        )
