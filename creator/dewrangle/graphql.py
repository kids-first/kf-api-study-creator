
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
