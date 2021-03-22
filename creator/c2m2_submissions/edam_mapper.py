import os
import logging
import requests
from owlready2 import get_ontology
from typing import Optional

logger = logging.getLogger(__name__)

EDAM_PATH = "./edam.owl"


def get_edam_mapping():
    """
    Build mapping of edam ontology to use for data type and file format
    encoding.
    """

    onto = get_ontology(
        "https://www.ebi.ac.uk/ols/ontologies/edam/download"
    ).load()

    mapping = {}
    for c in list(onto.classes()):
        if "data" not in c.get_name(c) and "format" not in c.get_name(c):
            continue
        for p in c.get_properties(c):

            if p._name == "label":
                mapping[p[c][0]] = c.get_name(c).replace("_", ":")

    return mapping


MAPPING = get_edam_mapping()

DATA_TYPES = {
    "Aligned Reads": "Alignment",
    "Aligned Reads Index": "Genome index",
    "Annotated Somatic Mutations": None,
    "Expression": "Expression data",
    "Gene Expression": "Expression data",
    "Gene Fusions": None,
    "gVCF": "Sequence variations",
    "gVCF Index": None,
    "Histology Images": "Image",
    "Isoform Expression": "Expression data",
    "Operation Reports": "Report",
    "Other": None,
    "Pathology Reports": "Report",
    "Radiology Images": "Report",
    "Radiology Reports": "Report",
    "Simple Nucleotide Variations": None,
    "Somatic Copy Number Variations": "Copy number variation",
    "Somatic Structural Variations": "Structural variation",
    "Unaligned Reads": "DNA sequence",
    "Variant Calls": "VCF",
    "Variant Calls Index": None,
}


def edam_data_type_mapper(v: Optional[str]) -> Optional[str]:
    data_type = MAPPING.get(v, None)
    if data_type is None:
        data_type = MAPPING.get(DATA_TYPES.get(v))
    # If the data: prefix is not there, we must have resolved a bad
    # value, like a file format, for instance.
    if data_type is not None and "data:" not in data_type:
        return None
    return data_type


def edam_file_format_mapper(v: Optional[str]) -> str:
    file_format = MAPPING.get(v, None)
    if file_format is None:
        # Often the dataservice file formats are just lowercased EDAM values
        file_format = MAPPING.get(v.upper(), None)

    if file_format is not None and "format:" not in file_format:
        return None

    return file_format
