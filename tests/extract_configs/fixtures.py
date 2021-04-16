from pprint import pformat

from creator.analyses.file_types import FILE_TYPES
from creator.studies.data_generator.study_generator import StudyGenerator

sg = StudyGenerator()
sg._create_dfs()


class MockAnalysis:
    def __init__(self, columns):
        self.columns = [{"name": c} for c in columns]


class MockFile:
    def __init__(self, file_type):
        self.file_type = file_type


class MockVersion:
    def __init__(self, valid_types=(), columns=(), file_type=None):
        self.analysis = MockAnalysis(columns)
        self.valid_types = set(valid_types)
        self.root_file = MockFile(file_type)


def make_template_df(file_type):
    """
    Return a DataFrame with content that conforms to one of the templated
    file types
    """
    dfs = {
        # Demographics
        "PDA": sg.dataframes["bio_manifest.tsv"],
        # Diseases
        "PTD": sg.dataframes["bio_manifest.tsv"],
        # Phenotypes
        "PTP": sg.dataframes["bio_manifest.tsv"],
        # General Observations
        "POB": sg.dataframes["bio_manifest.tsv"],
        # Outcomes
        "PTO": sg.dataframes["bio_manifest.tsv"],
        # Trios
        "FTR": sg.dataframes["bio_manifest.tsv"],
        # Complex relationships
        "FCM": sg.dataframes["bio_manifest.tsv"],
        # Sample manifest
        "SAM": sg.dataframes["bio_manifest.tsv"],
        # Sequencing manifest
        "SEQ": sg.dataframes["sequencing_manifest.tsv"],
        # Genomic files
        "S3S": sg.dataframes["s3_source_gf_manifest.tsv"],
        "GWO": sg.dataframes["gwo_manifest.tsv"],
    }
    df_keys = set(dfs.keys())
    ft_keys = set(FILE_TYPES.keys())
    assert df_keys <= ft_keys, (
        "Test fixture `make_template_df` is missing test Dataframes for "
        f"file types:{pformat(df_keys - ft_keys)}"
    )

    # Check that input file type has an existing test DataFrame
    try:
        df = dfs[file_type]
    except KeyError:
        ftname = FILE_TYPES[file_type]["name"]
        raise Exception(
            "A test DataFrame generator does not exist for file type "
            f"{file_type} {ftname}. Please define one and add it to "
            "`make_template_df` in tests/extract_configs/fixtures.py"
        )

    # Check that the df conforms to file type template
    missing = []
    for req_col in FILE_TYPES[file_type]["required_columns"]:
        if req_col not in df.columns:
            missing.append(req_col)
    if missing:
        raise Exception(
            f"Test DataFrame for file type {file_type} is missing required "
            f"columns: {missing}. Please modify the DataFrame "
            "builders in StudyGenerator._df_creators, which can be "
            "found in creator.studies.data_generator.study_generator"
        )
    return df
