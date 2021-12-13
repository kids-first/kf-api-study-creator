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
        except requests.exceptions.RequestException as e:
            logger.exception(
                f"Problem sending request to dewrangle {self.url}"
            )
            raise

        try:
            resp = response.json()
        except json.JSONDecodeError:
            logger.exception("Problem parsing JSON from response body")
            raise

        logger.debug(pformat(resp))

        return resp, response.status_code

    def _send_mutation(self, body, mutation_name):
        """
        Helper to send GraphQL mutation request and handle errors
        """
        resp, status_code = self._send_post_request(body)

        errors = (
            resp.get("data", {}).get(mutation_name, {}).get("errors")
        )
        if status_code != 200 or errors:
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

    def get_storage_analysis(self, obj_id):
        """
        Send graphql query to get a StorageAnalysis object from Dewrangle
        """
        pass

    def get_storage_analyses(self, study_id=None):
        """
        Send graphql query to get all StorageAnalysis objects or optionally,
        all StorageAnalysis objects for a particular study from Dewrangle
        """
        pass
