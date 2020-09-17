FILE_TYPES = {
    "OTH": {"name": "Other", "required_columns": [], "template": None},
    "SEQ": {
        "name": "Sequencing Manifest",
        "required_columns": [],
        "template": None,
    },
    "SHM": {
        "name": "Shipping Manifest",
        "required_columns": [],
        "template": None,
    },
    "CLN": {"name": "Clinical Data", "required_columns": [], "template": None},
    "DBG": {
        "name": "dbGaP Submission File",
        "required_columns": [],
        "template": None,
    },
    "FAM": {
        "name": "Familial Relationships",
        "required_columns": [],
        "template": None,
    },
    "S3S": {
        "name": "S3 Scrapes",
        "required_columns": ["Bucket", "Key", "Size", "ETag"],
        "template": "s3_scrape_config.py",
    },
    "PDA": {
        "name": "Participant Demographic and Administrative File",
        "required_columns": [
            "Participant ID",
            "Consent Short Name",
            "Administrative Gender",
            "Ethnicity",
            "Age at Study Enrollment",
            "Age at Study Enrollment Units",
            "Deceased",
            "Age at Last Contact",
            "Age at Last Contact Units",
        ],
        "template": "participant_config.py",
    },
    "FTR": {
        "name": "Family Trio",
        "required_columns": [
            "Participant ID",
            "Mother Participant ID",
            "Father Participant ID",
        ],
        "template": "family_trio_config.py",
    },
}
