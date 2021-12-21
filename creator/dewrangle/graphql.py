
STUDY_CREATE = """
  mutation ($input: StudyCreateInput!) {
    studyCreate(input: $input) {
      errors {
        message
      }
      study {
        id
        name
      }
    }
  }
"""

STUDY_UPDATE = """
  mutation ($id: ID!, $input: StudyUpdateInput!) {
    studyUpdate(id: $id, input: $input) {
      errors {
        message
      }
      study {
        id
        name
      }
    }
  }
"""

ORG_CREATE = """
  mutation ($input: OrganizationCreateInput!) {
    organizationCreate(input: $input) {
      errors {
        message
      }
      organization {
        id
        name
      }
    }
}
"""

ORG_UPDATE = """
  mutation ($id: ID!, $input: OrganizationUpdateInput!) {
    organizationUpdate(id: $id, input: $input) {
      errors {
        message
      }
      organization {
        id
        name
      }
    }
  }
"""

NODE_GET = """
  query($id: ID!) {
  		node(id: $id) {
      		id
  		}
  }
"""
