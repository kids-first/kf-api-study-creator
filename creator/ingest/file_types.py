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
    "CLN": {
        "name": "Clinical Data",
        "required_columns": [],
        "template": None,
    },
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
}
