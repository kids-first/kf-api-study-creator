import os
import csv
from creator.analyses.models import Analysis


KNOWN_FORMATS = {
    ".csv": "Comma Separated",
    ".tsv": "Tab Separated",
    ".xlsx": "Excel",
}


def analyze_version(version):
    """
    Attempt to open, parse, and summarize a file and create an analysis
    """
    data = version.key.read().decode()
    reader = csv.DictReader(data, delimiter="\t")

    data_format = determine_format(version)

    if data_format is None:
        return Analysis(version=version, known_format=False)

    with version.key.open(mode="rb") as f:
        rows = [r.decode() for r in f]
        reader = csv.DictReader(rows, delimiter="\t")

    analysis = Analysis(version=version, known_format=True)
    return analysis


def determine_format(version):
    _, extension = os.path.splitext(version.key.name)

    if extension in KNOWN_FORMATS:
        return [KNOWN_FORMATS[extension]]

    return None
