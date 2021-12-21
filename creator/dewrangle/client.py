import logging
import json
import os

import requests
from graphql import GraphQLError
from django.conf import settings
from pprint import pprint, pformat

from .graphql import *

logger = logging.getLogger(__name__)


class DewrangleClient(object):

    def __init__(self, personal_access_token=None, url=None):
        pat = personal_access_token or settings.DATA_TRACKER_DEWRANGLE_SECRET
        self.url = url or settings.DEWRANGLE_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Api-Key": pat,
                "Content-Type": "application/json"
            }
        )

    def _send_post_request(self, body):
        """
        Send POST request and parse response as json
        """
        try:
            response = self.session.post(self.url, json=body)
            response.raise_for_status()
        except Exception as e:
            logger.exception(
                f"Problem sending request to dewrangle {self.url}"
            )
            raise

        try:
            resp = response.json()
        except json.JSONDecodeError:
            logger.exception(
                "Problem parsing JSON from response body. Caused by:\n"
                f"{response.text}"
            )
            raise

        logger.debug(pformat(resp))

        return resp, response.status_code

    def _send_mutation(self, body, mutation_name):
        """
        Helper to send GraphQL mutation request and handle errors
        """
        resp, status_code = self._send_post_request(body)
        errors = resp.get("errors")

        if errors:
            msg = f"Failed {mutation_name} mutation @ {self.url}"
            logger.exception(msg)
            raise GraphQLError(
                f"{msg} Caused by:\n{errors}"
            )

        if "data" not in resp:
            raise GraphQLError(
                f"Unexpected response format. Caused by:\n{pformat(resp)}"
            )

        return resp, status_code

    def get_node(self, dewrangle_id):
        """
        Get a graphql object by id
        """
        body = {
            "query": NODE_GET.strip(),
            "variables": {
                "id": dewrangle_id
            }
        }
        resp, status_code = self._send_post_request(body)

        return resp.get("data", {}).get("node")

    def upsert_study(self, study):
        """
        Send graphql mutation to upsert a study in Dewrangle
        """
        node = self.get_node(study.dewrangle_id)
        if node:
            results = self.update_study(study)
        else:
            results = self.create_study(study)

        return results

    def create_study(self, study):
        """
        Send graphql mutation to create a study in Dewrangle
        """
        input_ = {
            attr: getattr(study, attr)
            for attr in ["name"]
        }
        input_["organizationId"] = study.organization.dewrangle_id
        body = {
            "query": STUDY_CREATE.strip(),
            "variables": {
                "input": input_
            }
        }

        mutation_name = "studyCreate"
        resp, status_code = self._send_mutation(body, mutation_name)
        results = resp["data"][mutation_name]["study"]

        study.dewrangle_id = results["id"]
        study.save()

        return results

    def update_study(self, study):
        """
        Send graphql mutation to update a study in Dewrangle
        """
        input_ = {
            attr: getattr(study, attr)
            for attr in ["name"]
        }
        body = {
            "query": STUDY_UPDATE.strip(),
            "variables": {
                "input": input_,
                "id": study.dewrangle_id
            }
        }

        mutation_name = "studyUpdate"
        resp, status_code = self._send_mutation(body, mutation_name)
        results = resp["data"][mutation_name]["study"]

        return results

    def upsert_organization(self, organization):
        """
        Send graphql mutation to upsert a organization in Dewrangle
        """
        node = self.get_node(organization.dewrangle_id)
        if node:
            results = self.update_organization(organization)
        else:
            results = self.create_organization(organization)

        return results

    def create_organization(self, organization):
        """
        Send graphql mutation to create an organization in Dewrangle
        """
        input_ = {
            attr: getattr(organization, attr)
            for attr in ["name"]
        }
        body = {
            "query": ORG_CREATE.strip(),
            "variables": {
                "input": input_
            }
        }

        mutation_name = "organizationCreate"
        resp, status_code = self._send_mutation(body, mutation_name)
        results = resp["data"][mutation_name]["organization"]

        organization.dewrangle_id = results["id"]
        organization.save()

        return results

    def update_organization(self, organization):
        """
        Send graphql mutation to update an organization in Dewrangle
        """
        input_ = {
            attr: getattr(organization, attr)
            for attr in ["name"]
        }
        body = {
            "query": ORG_UPDATE.strip(),
            "variables": {
                "input": input_,
                "id": organization.dewrangle_id
            }
        }

        mutation_name = "organizationUpdate"
        resp, status_code = self._send_mutation(body, mutation_name)
        results = resp["data"][mutation_name]["organization"]

        return results
