import copy
import logging
import requests
from requests.exceptions import RequestException
from django.conf import settings

from .models import Study

logger = logging.getLogger(__name__)


def sync_dataservice_studies():
    """
    Synchronizes studies in the dataservice with those in the Study Creator
    """
    api = settings.DATASERVICE_URL
    logger.info(f"Getting studies from Dataservice at {api}")
    try:
        resp = requests.get(f"{api}/studies?limit=100")
    except RequestException as err:
        logger.error(
            f"There was a problem getting studies from the Dataservice: {err}"
        )
        raise

    try:
        studies = copy.deepcopy(resp.json()["results"])
    except Exception as err:
        message = (
            f"There was a problem parsing the response from the "
            f"Dataservice: {err}"
        )
        logger.error(message)
        raise Exception(message)

    new_count = 0
    updated_count = 0
    for study in studies:
        fields = study
        del fields["_links"]

        if fields["name"] is None:
            fields["name"] = ""
        new_study, created = Study.objects.update_or_create(
            defaults=fields, kf_id=fields["kf_id"]
        )

        # If the study was found in the dataservice, it must not be deleted
        # This will allow us to 'recover' studies that have been deleted then
        # brought back
        new_study.deleted = False
        new_study.save()
        if created:
            new_count += 1
            logger.info(f"Created new Study: {study['kf_id']}")
        else:
            updated_count += 1

    ds_studies = {study["kf_id"] for study in studies}
    creator_studies = {study.kf_id for study in Study.objects.all()}
    deleted_studies = creator_studies - ds_studies

    for study in deleted_studies:
        Study.objects.filter(kf_id=study).update(deleted=True)

    logger.info(
        f"{new_count} studies created. "
        f"{updated_count} studies updated. "
        f"{len(deleted_studies)} studies deleted."
    )
