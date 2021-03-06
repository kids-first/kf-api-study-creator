"""
This is an extract config intended for S3 object manifests produced by TBD.

To use it, you must import it in another extract config and override at least
the `source_data_url`. You may also append additional operations to the
`operations` list as well.

For example you could have the following in your extract config module:

from kf_ingest_packages.common.extract_configs.s3_object_info import *

source_data_url = 'file://../data/kf-seq-data-bcm-chung-s3-objects.tsv'

operations.append(
    value_map(
        in_col='Key',
        out_col=CONCEPT.BIOSPECIMEN.ID,
        m=lambda x: x
    )
)
"""
import os

from kf_lib_data_ingest.common import constants
from kf_lib_data_ingest.common.constants import GENOMIC_FILE
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import (
    keep_map,
    row_map,
    value_map,
    constant_map,
)


def file_ext(x):
    """
    Get genomic file extension
    """
    matches = [
        file_ext for file_ext in FILE_EXT_FORMAT_MAP if x.endswith(file_ext)
    ]
    if matches:
        file_ext = max(matches, key=len)
    else:
        file_ext = None

    return file_ext


FILE_EXT_FORMAT_MAP = {
    "fq": GENOMIC_FILE.FORMAT.FASTQ,
    "fastq": GENOMIC_FILE.FORMAT.FASTQ,
    "fq.gz": GENOMIC_FILE.FORMAT.FASTQ,
    "fastq.gz": GENOMIC_FILE.FORMAT.FASTQ,
    "bam": GENOMIC_FILE.FORMAT.BAM,
    "hgv.bam": GENOMIC_FILE.FORMAT.BAM,
    "cram": GENOMIC_FILE.FORMAT.CRAM,
    "bam.bai": GENOMIC_FILE.FORMAT.BAI,
    "bai": GENOMIC_FILE.FORMAT.BAI,
    "cram.crai": GENOMIC_FILE.FORMAT.CRAI,
    "crai": GENOMIC_FILE.FORMAT.CRAI,
    "g.vcf.gz": GENOMIC_FILE.FORMAT.GVCF,
    "g.vcf.gz.tbi": GENOMIC_FILE.FORMAT.TBI,
    "vcf.gz": GENOMIC_FILE.FORMAT.VCF,
    "vcf": GENOMIC_FILE.FORMAT.VCF,
    "vcf.gz.tbi": GENOMIC_FILE.FORMAT.TBI,
    "peddy.html": "html",
}

DATA_TYPES = {
    GENOMIC_FILE.FORMAT.FASTQ: GENOMIC_FILE.DATA_TYPE.UNALIGNED_READS,
    GENOMIC_FILE.FORMAT.BAM: GENOMIC_FILE.DATA_TYPE.ALIGNED_READS,
    GENOMIC_FILE.FORMAT.CRAM: GENOMIC_FILE.DATA_TYPE.ALIGNED_READS,
    GENOMIC_FILE.FORMAT.BAI: "Aligned Reads Index",
    GENOMIC_FILE.FORMAT.CRAI: "Aligned Reads Index",
    GENOMIC_FILE.FORMAT.VCF: "Variant Calls",
    GENOMIC_FILE.FORMAT.GVCF: "gVCF",
    "g.vcf.gz.tbi": "gVCF Index",
    "vcf.gz.tbi": "Variant Calls Index",
    "html": "Other",
}


def filter_df_by_file_ext(df):
    """
    Only keep rows where file extension is one of those in
    FILE_EXT_FORMAT_MAP.keys
    """
    df[CONCEPT.GENOMIC_FILE.FILE_FORMAT] = df["Key"].apply(
        lambda x: file_format(x)
    )
    return df[df[CONCEPT.GENOMIC_FILE.FILE_FORMAT].notnull()]


source_data_url = (
    'https://localhost:5002/download/study/SD_ME0WME0W/'
    'file/SF_Y1JMXTTS/version/FV_4RYEMD71'
)

do_after_read = filter_df_by_file_ext


def s3_url(row):
    """
    Create S3 URL for object from S3 bucket and key
    """
    return f's3://{row["Bucket"]}/{row["Key"]}'


def file_format(x):
    """
    Get genomic file format by looking genomic file ext up in
    FILE_EXT_FORMAT_MAP dict
    """
    # File format
    return FILE_EXT_FORMAT_MAP.get(file_ext(x))


def data_type(x):
    """
    Get genomic file data type by looking up file format in DATA_TYPES.
    However, if the file's extension has `tbi` in it, then use the file
    extension itself to do the data type lookup.
    """
    ext = file_ext(x)
    if "tbi" in ext:
        data_type = DATA_TYPES.get(ext)
    else:
        data_type = DATA_TYPES.get(file_format(x))

    return data_type


operations = [
    row_map(out_col=CONCEPT.GENOMIC_FILE.ID, m=lambda row: s3_url(row)),
    row_map(
        out_col=CONCEPT.GENOMIC_FILE.URL_LIST, m=lambda row: [s3_url(row)]
    ),
    value_map(
        in_col="Key",
        out_col=CONCEPT.GENOMIC_FILE.FILE_NAME,
        m=lambda x: os.path.split(x)[-1],
    ),
    keep_map(in_col="Size", out_col=CONCEPT.GENOMIC_FILE.SIZE),
    value_map(
        in_col="ETag",
        out_col=CONCEPT.GENOMIC_FILE.HASH_DICT,
        m=lambda x: {constants.FILE.HASH.S3_ETAG.lower(): x.replace('"', "")},
    ),
    constant_map(
        out_col=CONCEPT.GENOMIC_FILE.AVAILABILITY,
        m=constants.GENOMIC_FILE.AVAILABILITY.IMMEDIATE,
    ),
    keep_map(
        in_col=CONCEPT.GENOMIC_FILE.FILE_FORMAT,
        out_col=CONCEPT.GENOMIC_FILE.FILE_FORMAT,
    ),
    value_map(
        in_col="Key",
        out_col=CONCEPT.GENOMIC_FILE.DATA_TYPE,
        m=lambda x: data_type(x),
    ),
]
