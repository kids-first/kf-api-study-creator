"""
This is an extract configuration for a Sequencing Manifest file

See: https://www.notion.so/d3b/Internal-File-Types-and-Guidelines-6edd92087f04445e84a236202831edbd#aa2c7d8a50164a08ab685b42b784293e

Required Columns:
    Aliquot ID
    Source Sequencing Filepath
    Sequencing Center
    Reference Genome
    Analyte Type
    Experiment Name
    Experiment Strategy
    Experiment Date
    Instrument Model
    Library Name
    Library Platform
    Library Strand
    Library Selection
    Library Prep
    Is Paired End
    Max Insert Size
    Mean Insert Size
    Mean Depth
    Total Reads
    Mean Read Length
"""
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import (
    keep_map,
    value_map,
    constant_map
)

source_data_url = "{{ download_url }}"

operations = [
    keep_map(
        in_col="Aliquot ID", out_col=CONCEPT.BIOSPECIMEN.ID
    ),
    keep_map(
        in_col="Source Sequencing Filepath",
        out_col=CONCEPT.GENOMIC_FILE.ID,
    ),
    keep_map(
        in_col="Sequencing Center",
        out_col=CONCEPT.SEQUENCING.CENTER.NAME,
    ),
    keep_map(
        in_col="Analyte Type",
        out_col=CONCEPT.BIOSPECIMEN.ANALYTE,
    ),
    keep_map(
        in_col="Experiment Name",
        out_col=CONCEPT.SEQUENCING.ID,
    ),
    keep_map(
        in_col="Experiment Strategy",
        out_col=CONCEPT.SEQUENCING.STRATEGY,
    ),
    keep_map(
        in_col="Experiment Date",
        out_col=CONCEPT.SEQUENCING.DATE,
    ),
    keep_map(
        in_col="Instrument Model",
        out_col=CONCEPT.SEQUENCING.INSTRUMENT,
    ),
    keep_map(
        in_col="Library Name",
        out_col=CONCEPT.SEQUENCING.LIBRARY_NAME,
    ),
    keep_map(
        in_col="Library Platform",
        out_col=CONCEPT.SEQUENCING.PLATFORM,
    ),
    keep_map(
        in_col="Library Strand",
        out_col=CONCEPT.SEQUENCING.LIBRARY_STRAND,
    ),
    keep_map(
        in_col="Library Selection",
        out_col=CONCEPT.SEQUENCING.LIBRARY_SELECTION,
    ),
    keep_map(
        in_col="Library Prep",
        out_col=CONCEPT.SEQUENCING.LIBRARY_PREP,
    ),
    keep_map(
        in_col="Max Insert Size",
        out_col=CONCEPT.SEQUENCING.MAX_INSERT_SIZE,
    ),
    keep_map(
        in_col="Mean Insert Size",
        out_col=CONCEPT.SEQUENCING.MEAN_INSERT_SIZE,
    ),
    keep_map(
        in_col="Mean Depth",
        out_col=CONCEPT.SEQUENCING.MEAN_DEPTH,
    ),
    keep_map(
        in_col="Total Reads",
        out_col=CONCEPT.SEQUENCING.TOTAL_READS,
    ),
    keep_map(
        in_col="Mean Read Length",
        out_col=CONCEPT.SEQUENCING.MEAN_READ_LENGTH,
    ),
    constant_map(
        m=False,
        out_col=CONCEPT.GENOMIC_FILE.HARMONIZED,
    ),
    keep_map(
        in_col="Reference Genome",
        out_col=CONCEPT.GENOMIC_FILE.REFERENCE_GENOME,
    ),
    keep_map(
        in_col="Is Paired End",
        out_col=CONCEPT.SEQUENCING.PAIRED_END,
    ),
]
