"""
This is an extract configuration for a Biobank Manifest

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import keep_map

source_data_url = "{{ download_url }}"

operations = [
    keep_map(in_col="Specimen ID", out_col=CONCEPT.BIOSPECIMEN_GROUP.ID),
    keep_map(
        in_col="Aliquot ID", out_col=CONCEPT.BIOSPECIMEN.ID
    ),
    keep_map(
        in_col="Analyte Type",
        out_col=CONCEPT.BIOSPECIMEN.ANALYTE,
    ),
    keep_map(
        in_col="Quantity Value",
        out_col=CONCEPT.BIOSPECIMEN.VOLUME_UL,
        optional=True,
    ),
    keep_map(
        in_col="Concentration Value",
        out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION_MG_PER_ML,
        optional=True,
    ),
    # Not supported, by concept schema or Dataservice yet
    # keep_map(
    #     in_col="Quantity Value",
    #     out_col=CONCEPT.BIOSPECIMEN.QUANTITY.VALUE,
    # ),
    # keep_map(
    #     in_col="Quantity Units",
    #     out_col=CONCEPT.BIOSPECIMEN.QUANTITY.UNITS,
    # ),
    # keep_map(
    #     in_col="Concentration Value",
    #     out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION.VALUE,
    # ),
    # keep_map(
    #     in_col="Concentration Units",
    #     out_col=CONCEPT.BIOSPECIMEN.CONCENTRATION.UNITS,
    # ),
    # keep_map(
    #     in_col="Preservation Method",
    #     out_col=CONCEPT.BIOSPECIMEN.PRESERVATION_METHOD,
    # ),
    # keep_map(
    #     in_col="Availibility Status",
    #     out_col=CONCEPT.BIOSPECIMEN.PRESERVATION_METHOD,
    # ),
]
