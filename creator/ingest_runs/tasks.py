from creator.ingest_runs.manifests import ingest_manifest

import requests


def run_ingest(ingest_run_id):
    # TODO
    print(f"Preparing ingest run {ingest_run_id}")


def cancel_ingest(ingest_run_id):
    # TODO
    print(f"Cancelling ingest run {ingest_run_id}")


def ingest_genomic_workflow_output_manifests(versions):
    print(f"Begin ingesting genomic workflow manifests: {versions}")
    """
    for version in versions:
        ingest_manifest(version)
    """

    hi = requests.get('http://localhost:5000/studies/SD_BHJXBDQK').json()
    print(hi)
