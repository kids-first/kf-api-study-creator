import os
import csv
from collections import defaultdict
from creator.analyses.models import Analysis


KNOWN_FORMATS = {
    ".csv": "Comma Separated",
    ".tsv": "Tab Separated",
    ".xlsx": "Excel",
}

NUMBER_OF_COMMON_VALUES = 15


def analyze_version(version):
    """
    Attempt to open, parse, and summarize a file and create an analysis
    """
    # If the version already has an analysis, update it or else create a new
    # anaylis in the database.
    if version.analysis:
        analysis = version.analysis
    else:
        analysis = Analysis
        analysis.version = version

    data = version.key.read().decode()
    reader = csv.DictReader(data, delimiter="\t")

    data_format = determine_format(version)

    if data_format is None:
        analysis.known_format = False
        return analysis

    # These are the three metrics we will compute and return
    # Keyed by column
    distincts = defaultdict(set)
    # Keyed by column and then value
    counts = defaultdict(lambda: defaultdict(int))
    nrows = 0
    ncols = 0

    with version.key.open(mode="rb") as f:
        rows = [r.decode() for r in f]
        reader = csv.DictReader(rows, delimiter="\t")

        for row in reader:
            for k, v in row.items():
                distincts[k].add(v)
                counts[k][v] += 1

        nrows = len(rows)
        ncols = len(distincts.keys())

    columns = []
    for k, v in distincts.items():
        common_values = sorted(
            counts[k].items(), key=lambda x: x[1], reverse=True
        )[:NUMBER_OF_COMMON_VALUES]
        col = {
            "name": k,
            "distinct_values": len(v),
            "common_values": [v[0] for v in common_values],
        }
        columns.append(col)

    analysis.known_format = True
    analysis.columns = columns
    analysis.nrows = nrows

    analysis.ncols = ncols
    return analysis


def determine_format(version):
    _, extension = os.path.splitext(version.key.name)

    if extension in KNOWN_FORMATS:
        return [KNOWN_FORMATS[extension]]

    return None
