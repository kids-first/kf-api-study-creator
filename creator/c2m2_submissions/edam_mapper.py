import os
import csv
import logging
import requests
from dataclasses import dataclass
from owlready2 import get_ontology
from typing import Optional, TypedDict, Dict

logger = logging.getLogger(__name__)

EDAM_PATH = "./edam.owl"

Entry = TypedDict("Entry", {"label": str, "description": str})


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


class EDAMMapper:
    def __init__(
        self,
        edam_url: str = "https://www.ebi.ac.uk/ols/ontologies/edam/download",
    ):
        self.edam_url = edam_url
        self._onto = None
        self._mapping: Dict[str, Entry] = None

    @property
    def onto(self):
        """
        Load the EDAM ontology if it has not yet been loaded
        """
        if self._onto is None:
            self._onto = get_ontology(self.edam_url).load()

        return self._onto

    def write(self, out_dir: str):

        # Write out the file formats
        with open(os.path.join(out_dir, "file_format.tsv"), "w") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            writer.writerow(["id", "name", "description"])
            for name, entry in self.mapping.items():
                if "format:" in entry["label"]:
                    writer.writerow([entry["label"], name, name])

        # Write out data types
        with open(os.path.join(out_dir, "data_type.tsv"), "w") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")

            writer.writerow(["id", "name", "description"])
            for name, entry in self.mapping.items():
                if "data:" in entry["label"]:
                    writer.writerow([entry["label"], name, name])

    def _get_edam_mapping(self) -> Dict[str, Entry]:
        """
        Build mapping of edam ontology to use for data type and file format
        encoding.
        """

        mapping = {}
        for c in list(self.onto.classes()):
            if "data_" not in c.get_name(c) and "format_" not in c.get_name(c):
                continue

            entry = {}
            name = None
            for p in c.get_properties(c):
                if p._name == "label":
                    entry["label"] = c.get_name(c).replace("_", ":")
                    name = p[c][0]
                if p._name == "hasDefinition":
                    entry["description"] = p[c][0]

            mapping[name] = entry
        return mapping

    @property
    def mapping(self):
        if self._mapping is None:
            self._mapping = self._get_edam_mapping()

        return self._mapping

    def map_data_type(self, v: Optional[str]) -> Optional[str]:
        data_type = self.mapping.get(v, None)
        if data_type is None:
            data_type = self.mapping.get(DATA_TYPES.get(v.upper()))

        if data_type is not None:
            # If the data: prefix is not there, we must have resolved a bad
            # value, like a file format, for instance.
            if "data:" not in data_type["label"]:
                return None
            return data_type["label"]

    def map_file_format(self, v: Optional[str]) -> str:
        file_format = self.mapping.get(v, None)
        if file_format is None:
            # Often the dataservice file formats are just lowercased EDAM
            file_format = self.mapping.get(v.upper(), None)

        if file_format is not None:
            if "format:" not in file_format["label"]:
                return None
            return file_format["label"]
