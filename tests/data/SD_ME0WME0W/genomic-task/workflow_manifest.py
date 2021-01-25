##########################################################
# Generate a sample Genomic Workflow Output Manifest
# for the test study. This script must be run after the
# tabular data is loaded into the local DataService, as
# this manifest requires KF IDs.
##########################################################

import os
import pandas as pd
import random as ra

import requests
from collections import defaultdict
from kf_utils.dataservice.scrape import yield_entities
from string import hexdigits

TARGET_SERVICE = "http://localhost:5000"


def create_hex(n):
    """
    Return a random hex number of length n.
    """
    return "".join([ra.choice(hexdigits).lower() for _ in range(n)])


def get_gen_from_biospec(biospec):
    """
    Get the associated GenomicFile data and return it for a given
    biospec.
    """
    gen_link = biospec['_links']['genomic_files']
    resp = requests.get(
        f'{TARGET_SERVICE}{gen_link}',
        headers={'Content-Type': 'application/json'},
    )
    return resp.json()['results']


def harmonized_path(unharmonized_path):
    """
    Generate the path to a harmonized GenomicFile associated with the
    unharmonized GenomicFile located at _unharmonized_path_ and return it.
    """
    _, filename = os.path.split(unharmonized_path)
    S3_HARMONIZED = (
        's3://kf-study-us-east-1-prd-sd-me0wme0w/harmonized/simple-variants/'
    )
    return f'{S3_HARMONIZED}{filename}.gz'


def create_manifest():
    manifest_data = defaultdict(list)

    # Get the Biospeciments from DataService
    biospecs = list(yield_entities(
        TARGET_SERVICE,
        'biospecimens',
        {
            "study_id": "SD_ME0WME0W",
            "visible": True
        }
    ))
    for biospec in biospecs:
        for gen_file in get_gen_from_biospec(biospec):
            if gen_file['external_id'].endswith('.cram'):
                manifest_data['Cavatica ID'].append(create_hex(25))
                manifest_data['Cavatica Task ID'].append(
                    "-".join([create_hex(i) for i in [8, 4, 4, 4, 12]])
                )
                manifest_data['KF Biospecimen ID'].append(biospec['kf_id'])
                manifest_data['KF Participant ID'].append(
                    biospec['_links']['participant'].split('/')[-1]
                )
                manifest_data['KF Family ID'].append(None)
                # Generate the filepath of the harmonized genomic file from
                # the filepath of the associated unharmonized genomic file
                manifest_data['Filepath'].append(
                    harmonized_path(gen_file['external_id'])
                )
                manifest_data['Data Type'].append('gVCF')
                manifest_data['Workflow Type'].append('alignment')
                manifest_data['Source Read'].append(gen_file['external_id'])

    pd.DataFrame(manifest_data).to_csv(
        "workflow.tsv",
        index=False,
        sep='\t',
    )


if __name__ == '__main__':
    create_manifest()

