import logging
import json
import os

import requests
from graphql import GraphQLError
from django.conf import settings

from .graphql import *

logger = logging.getLogger(__name__)


class DewrangleClient(object):

    def __init__(self, personal_access_token=None, url=None):
        pat = personal_access_token or settings.DATA_TRACKER_DEWRANGLE_TOKEN
        self.url = url or settings.DEWRANGLE_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Api-Key": pat,
                "Content-Type": "application/json"
            }
        )

    def bulk_create_file_upload_invoices(self, study_id, invoices):
        """
        Send graphql mutation to create a batch of file upload invoices
        in Dewrangle
        """
        body = {
            "query": FILE_UPLOAD_INVOICE_CREATE.strip(),
            "variables": {
                "input": {
                    "studyId": study_id,
                    "fileUploadInvoices": invoices
                }
            }
        }
        try:
            response = self.session.post(self.url, json=body)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.exception(
                f"Problem sending request to dewrangle {self.url}"
            )
            raise

        try:
            data = response.json()["data"]
        except json.exceptions.JSONDecodeError:
            logger.exception("Problem parsing JSON from response body")
            raise

        if response.status_code != 200 or "errors" in data:
            msg = "There was a problem creating file upload invoices."
            logger.exception(msg)
            raise GraphQLError(
                f"{msg} Caused by:\n{data['errors']}"
            )

        results = data["fileUploadInvoiceCreate"]["fileUploadInvoices"]

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
