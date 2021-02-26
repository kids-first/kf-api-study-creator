import os
import csv
import xlrd
from collections import defaultdict
from functools import partial
from django.conf import settings
from django_s3_storage.storage import S3Storage
from graphql import GraphQLError
from creator.analyses.models import Analysis
from creator.files.models import Version


def XLSXDictReader(data):
    data = data.read()
    book = xlrd.open_workbook(file_contents=data)
    sheet = book.sheet_by_index(0)
    headers = dict((i, sheet.cell_value(0, i)) for i in range(sheet.ncols))

    return (
        dict((headers[j], sheet.cell_value(i, j)) for j in headers)
        for i in range(1, sheet.nrows)
    )


def CSVDictReader(data, delimiter=","):
    data = [r.decode() for r in data]
    return csv.DictReader(data, delimiter=delimiter)


KNOWN_FORMATS = {
    ".csv": {"name": "Comma Separated", "reader": CSVDictReader},
    ".tsv": {
        "name": "Tab Separated",
        "reader": partial(CSVDictReader, delimiter="\t"),
    },
    ".xlsx": {"name": "Excel", "reader": XLSXDictReader},
    ".xls": {"name": "Excel", "reader": XLSXDictReader},
}

NUMBER_OF_COMMON_VALUES = 15


def analyze_version(version):
    """
    Attempt to open, parse, and summarize a file and create an analysis
    """
    # If the version already has an analysis, update it or else create a new
    # analyis in the database.
    try:
        analysis = version.analysis
    except Analysis.DoesNotExist:
        analysis = Analysis()
        version.analysis = analysis

    try:
        content = extract_data(version)
    except Exception as err:
        analysis.known_format = False
        analysis.error_message = err
        return analysis

    # These are the three metrics we will compute and return
    # Keyed by column
    distincts = defaultdict(set)
    # Keyed by column and then value
    counts = defaultdict(lambda: defaultdict(int))
    nrows = 0
    ncols = 0

    for row in content:
        for k, v in row.items():
            distincts[k].add(v)
            counts[k][v] += 1

        nrows = len(content)
        ncols = len(distincts.keys())

    # Compile statistics on each column
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


def extract_data(version):
    """
    Determine what file type the file is and attempt to extract it into rows
    of data returned in a DictReader type interface.
    """
    _, data_format = os.path.splitext(version.key.name)

    if data_format not in KNOWN_FORMATS:
        raise IOError(f"{data_format} is not an understood data format.")

    # Need to set storage location for study bucket if using S3 backend
    if settings.DEFAULT_FILE_STORAGE == "django_s3_storage.storage.S3Storage":
        if version.study is not None:
            study = version.study
        elif version.root_file is not None:
            study = version.root_file.study
        else:
            raise GraphQLError("Version must be part of a study.")

        version.key.storage = S3Storage(aws_s3_bucket_name=study.bucket)

    with version.key.open(mode="rb") as f:
        parsed = list(KNOWN_FORMATS[data_format]["reader"](f))

    return parsed
