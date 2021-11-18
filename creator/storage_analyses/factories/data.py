import os
import random
import hashlib
import pandas
import uuid
from pprint import pprint

from kf_lib_data_ingest.common.constants import GENOMIC_FILE


FILE_EXT_FORMAT_MAP = {
    'fq': GENOMIC_FILE.FORMAT.FASTQ,
    'fastq': GENOMIC_FILE.FORMAT.FASTQ,
    'fq.gz': GENOMIC_FILE.FORMAT.FASTQ,
    'fastq.gz': GENOMIC_FILE.FORMAT.FASTQ,
    'bam': GENOMIC_FILE.FORMAT.BAM,
    'hgv.bam': GENOMIC_FILE.FORMAT.BAM,
    'cram': GENOMIC_FILE.FORMAT.CRAM,
    'bam.bai': GENOMIC_FILE.FORMAT.BAI,
    'bai': GENOMIC_FILE.FORMAT.BAI,
    'cram.crai': GENOMIC_FILE.FORMAT.CRAI,
    'crai': GENOMIC_FILE.FORMAT.CRAI,
    'g.vcf.gz': GENOMIC_FILE.FORMAT.GVCF,
    'g.vcf.gz.tbi': GENOMIC_FILE.FORMAT.TBI,
    'vcf.gz': GENOMIC_FILE.FORMAT.VCF,
    'vcf': GENOMIC_FILE.FORMAT.VCF,
    'vcf.gz.tbi': GENOMIC_FILE.FORMAT.TBI,
}

DATA_TYPES = {
    GENOMIC_FILE.FORMAT.FASTQ: GENOMIC_FILE.DATA_TYPE.UNALIGNED_READS,
    GENOMIC_FILE.FORMAT.BAM: GENOMIC_FILE.DATA_TYPE.ALIGNED_READS,
    GENOMIC_FILE.FORMAT.CRAM: GENOMIC_FILE.DATA_TYPE.ALIGNED_READS,
    GENOMIC_FILE.FORMAT.BAI: 'Aligned Reads Index',
    GENOMIC_FILE.FORMAT.CRAI: 'Aligned Reads Index',
    GENOMIC_FILE.FORMAT.VCF: 'Variant Calls',
    GENOMIC_FILE.FORMAT.GVCF: 'gVCF',
    'g.vcf.gz.tbi': 'gVCF Index',
    'vcf.gz.tbi': 'Variant Calls Index'
}

GB_1 = 1024**3


def hash_file(url):
    """
    Create fake hash from file url
    """
    m = hashlib.md5()
    m.update(url.encode("utf-8"))
    return m.hexdigest()


def filename():
    """
    Use uuid for filename and random extension from list
    """
    choices = list(FILE_EXT_FORMAT_MAP.keys()) + ["pdf", "svs"]
    return (
        f"{uuid.uuid4()}.{random.choice(choices)}"
    )


def make_df(study_id, nrows=5, created_at=1):
    """
    Make a DataFrame that can be used to produce either a file upload manifest
    or S3 inventory
    """
    study_id = study_id.replace("_", "-").lower()

    def make_row(i):
        fn = filename()
        hash_val = hash_file(fn)
        siz = random.randint(GB_1*10, GB_1*100)
        return {
            "Source File Name": fn,
            "Bucket": f"kf-study-us-east-1-prd-{study_id}",
            "Key": f"data/{fn}",
            "Hash": hash_val,
            "Hash Algorithm": "md5",
            "Size": siz,
            "Aliquot ID": f"SAM-00{i}"
        }
    rows = []
    for i in range(nrows):
        rows.append(make_row(i))
    df = pandas.DataFrame(rows)
    df["Created At"] = created_at

    return df


def upload_manifest_df(df):
    """
    Create a file upload manifest DataFrame from the output of make_df
    """
    return df.drop(columns=["Bucket", "Key"])


def inventory_df(df):
    """
    Create a S3 inventory DataFrame from the output of make_df
    """
    return df.drop(columns=["Source File Name", "Aliquot ID"])


def make_files(n_manifests=2, n_uploads=3, study_id="SD_ME0WME0W"):
    """
    Create fake file upload manifests and an S3 inventory
    """
    # Create upload manifests
    dfs = [make_df(study_id, n_uploads, created_at=i)
           for i in range(n_manifests)]
    uploads = [upload_manifest_df(df) for df in dfs]

    # Create inventory
    inventory = inventory_df(pandas.concat(dfs)).copy()

    # Remove some files
    inventory = inventory.iloc[0:int(
        n_manifests*n_uploads*.80)].reset_index(drop=True)

    # Rename some files
    for i in range(int(n_manifests*n_uploads*.10)):
        inventory.at[i, 'Key'] = "data/" + filename()

    # Add some unexpected files
    nunexpected = int(n_manifests*n_uploads*.10)
    inventory = pandas.concat(
        [inventory, inventory_df(make_df(study_id, nrows=nunexpected))],
        ignore_index=True
    )

    return uploads, inventory
