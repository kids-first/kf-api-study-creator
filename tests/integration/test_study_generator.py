import os
import pytest
import requests

from creator.ingest_runs.data_generator.study_generator import (
    ENDPOINTS,
    delete_entities,
)
from tests.integration.fixtures import (
    LOCAL_DATASERVICE_URL,
    test_study_generator,
    dataservice_setup,
)


def test_delete_entities():
    """
    Test study_generator.delete_entities
    """
    # Delete all studies
    delete_entities(LOCAL_DATASERVICE_URL)

    # Setup
    n = 3
    np = 2
    data = {
        "studies": [
            {"external_id": f"study_{i}", "kf_id": f"SD_{i}1111111"}
            for i in range(n)
        ],
        "participants": [
            {"kf_id": f"PT_{i}{j}111111", "gender": "Female",
             "study_id": f"SD_{i}1111111"}
            for i in range(n)
            for j in range(np)
        ]
    }
    for endpoint, payloads in data.items():
        for p in payloads:
            resp = requests.post(
                f"{LOCAL_DATASERVICE_URL}/{endpoint}", json=p
            )

    # Delete one study
    kfid = data["studies"][0]["kf_id"]
    delete_entities(LOCAL_DATASERVICE_URL, study_id=kfid)

    # Check study 1 deleted, study 2,3 remain
    for i in range(n):
        kfid = data["studies"][i]["kf_id"]
        params = {"study_id": kfid}
        study_resp = requests.get(f"{LOCAL_DATASERVICE_URL}/studies/{kfid}")
        part_resp = requests.get(
            f"{LOCAL_DATASERVICE_URL}/participants", params=params
        )
        if i == 0:
            assert study_resp.status_code == 404
            assert part_resp.json()["total"] == 0
        else:
            assert study_resp.status_code == 200
            assert part_resp.json()["total"] == np

    # Delete all studies
    delete_entities(LOCAL_DATASERVICE_URL)

    # Check all study entities deleted
    for endpoint in ENDPOINTS:
        resp = requests.get(f"{LOCAL_DATASERVICE_URL}/{endpoint}")
        assert resp.json()["total"] == 0


def test_end_to_end(tmpdir, test_study_generator, dataservice_setup):
    """
    Basic testing of StudyGenerator.ingest_study
    """
    sg = test_study_generator(study_id="SD_YE0WYE0W", total_specimens=5)
    sg.ingest_study()

    # Check Data Service entity counts
    for endpoint, count in sg.expected_counts.items():
        params = {"study_id": sg.study_id}
        resp = requests.get(
            f"{sg.dataservice_url}/{endpoint}", params=params
        )
        assert resp.json()["total"] == sg.expected_counts[endpoint]

    # Check ingest package dir and data files
    for fn in sg.dataframes:
        assert os.path.exists(os.path.join(sg.data_dir, fn))
