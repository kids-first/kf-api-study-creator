import pytest
from creator.organizations.factories import OrganizationFactory


@pytest.fixture(autouse=True)
def default_organization(db):
    """ Creates a default org"""

    organization = OrganizationFactory()
    return organization
