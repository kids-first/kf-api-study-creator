#########################################################
# Load the study and sequencing center into the
# Dataservice. This must be done manually each time the
# container is taken down and brought back up again.
#########################################################

from pprint import pprint
import requests

def load():
    """
    Load the two mandatory entities.
    """
    URL = "http://localhost:5000"
    headers = {"Content-Type": "application/json"}
    study_body = {
        "kf_id": "SD_ME0WME0W",
        "name": "MEOW",
        "external_id": "MEOW",
    }
    study_resp = requests.post(
        f"{URL}/studies",
        headers=headers,
        json=study_body
    )
    pprint(study_resp.json())

    center_body = {
        "kf_id": "SC_DGDDQVYR",
        "name": "Broad Institute",
        "external_id": "Broad",
    }
    center_resp = requests.post(
        f"{URL}/sequencing-centers",
        headers=headers,
        json=center_body,
    )
    pprint(center_resp.json())


if __name__ == "__main__":
    load()



