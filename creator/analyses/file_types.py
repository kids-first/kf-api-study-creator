FILE_TYPES = {
    "OTH": {"name": "Other", "required_columns": [], "template": None},
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
    "FCM": {
        "name": "Complex Family",
        "required_columns": [
            "First Participant ID",
            "Second Participant ID",
            "Relationship from First to Second",
        ],
        "template": "complex_family_config.py",
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
    "PDA": {
        "name": "Participant Details",
        "required_columns": [
            "Participant ID",
            "Clinical Sex",
            "Affected Status",
            "Proband",
        ],
        "template": "participant_config.py",
    },
    "GOB": {
        "name": "General Observations",
        "required_columns": [
            "Participant ID",
            "Observation Name",
            "Category",
            "Status",
        ],
        "template": "general_observations_config.py",
    },
    "PTD": {
        "name": "Participant Diseases",
        "required_columns": [
            "Participant ID",
            "Condition Name",
            "Category",
        ],
        "template": "participant_diseases_config.py",
    },
    "PTP": {
        "name": "Participant Phenotypes",
        "required_columns": [
            "Participant ID",
            "Condition Name",
            "Verification Status",
        ],
        "template": "participant_phenotypes_config.py",
    },
    "ALM": {
        "name": "Aliquot Manifest",
        "required_columns": [
            "Specimen ID",
            "Aliquot ID",
            "Analyte Type",
            "Sequencing Center",
        ],
        "template": "aliquot_manifest_config.py",
    },
    "BBM": {
        "name": "Biobank Manifest",
        "required_columns": ["Specimen ID", "Aliquot ID", "Analyte Type"],
        "template": "biobank_manifest_config.py",
    },
    "BCM": {
        "name": "Biospecimen Collection Manifest",
        "required_columns": [
            "Participant ID",
            "Specimen ID",
            "Composition Name",
            "Body Site Name",
        ],
        "template": "biospecimen_collection_manifest_config.py",
    },
    "SEQ": {
        "name": "Sequencing File Manifest",
        "required_columns": [
            "Aliquot ID",
            "Sequencing Center",
            "Sequencing Output Filepath",
            "Reference Genome",
            "Experiment Strategy",
            "Sequencing Library Name",
            "Sequencing Platform",
            "Is Paired End",
        ],
        "template": "sequencing_manifest_config.py",
    },
    "S3S": {
        "name": "S3 Scrapes",
        "required_columns": ["Bucket", "Key", "Size", "ETag"],
        "template": "s3_scrape_config.py",
    },
    "GWO": {
        "name": "Genomic Workflow Output Manifest",
        "required_columns": [
            "Cavatica ID",
            "Cavatica Task ID",
            "KF Biospecimen ID",
            "KF Participant ID",
            "KF Family ID",
            "Filepath",
            "Data Type",
            "Workflow Type",
            "Source Read",
        ],
        "template": "genomic_workflow_output_manifest_config.py",
    },
}
