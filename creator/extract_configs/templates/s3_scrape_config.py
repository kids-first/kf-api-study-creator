"""
This is an extract configuration for a S3 Scrape file.

See template definitions here:
https://docs.google.com/spreadsheets/d/1ugcw1Rh3e7vXnc7OWlR4J7bafiBjGnfd4-rEThI-BNI
"""
from kf_lib_data_ingest.common import constants
from kf_lib_data_ingest.common.constants import GENOMIC_FILE, COMMON
from kf_lib_data_ingest.common.concept_schema import CONCEPT
from kf_lib_data_ingest.etl.extract.operations import (
    keep_map,
    row_map,
    value_map,
    constant_map,
)


def genomic_file_ext(x):
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
    ".fq": GENOMIC_FILE.FORMAT.FASTQ,
    ".fastq": GENOMIC_FILE.FORMAT.FASTQ,
    ".fq.gz": GENOMIC_FILE.FORMAT.FASTQ,
    ".fastq.gz": GENOMIC_FILE.FORMAT.FASTQ,
    ".bam": GENOMIC_FILE.FORMAT.BAM,
    ".hgv.bam": GENOMIC_FILE.FORMAT.BAM,
    ".cram": GENOMIC_FILE.FORMAT.CRAM,
    ".bam.bai": GENOMIC_FILE.FORMAT.BAI,
    ".bai": GENOMIC_FILE.FORMAT.BAI,
    ".cram.crai": GENOMIC_FILE.FORMAT.CRAI,
    ".crai": GENOMIC_FILE.FORMAT.CRAI,
    ".g.vcf.gz": GENOMIC_FILE.FORMAT.GVCF,
    ".g.vcf.gz.tbi": GENOMIC_FILE.FORMAT.TBI,
    ".vcf.gz": GENOMIC_FILE.FORMAT.VCF,
    ".vcf": GENOMIC_FILE.FORMAT.VCF,
    ".vcf.gz.tbi": GENOMIC_FILE.FORMAT.TBI,
    ".peddy.html": GENOMIC_FILE.FORMAT.HTML,
    ".md5": COMMON.OTHER,
}

DATA_TYPES = {
    GENOMIC_FILE.FORMAT.FASTQ: GENOMIC_FILE.DATA_TYPE.UNALIGNED_READS,
    GENOMIC_FILE.FORMAT.BAM: GENOMIC_FILE.DATA_TYPE.ALIGNED_READS,
    GENOMIC_FILE.FORMAT.CRAM: GENOMIC_FILE.DATA_TYPE.ALIGNED_READS,
    GENOMIC_FILE.FORMAT.BAI: GENOMIC_FILE.DATA_TYPE.ALIGNED_READS_INDEX,
    GENOMIC_FILE.FORMAT.CRAI: GENOMIC_FILE.DATA_TYPE.ALIGNED_READS_INDEX,
    GENOMIC_FILE.FORMAT.VCF: GENOMIC_FILE.DATA_TYPE.VARIANT_CALLS,
    GENOMIC_FILE.FORMAT.GVCF: GENOMIC_FILE.DATA_TYPE.GVCF,
    GENOMIC_FILE.FORMAT.HTML: COMMON.OTHER,
    # Different TBI types share the same format in FILE_EXT_FORMAT_MAP above
    ".g.vcf.gz.tbi": GENOMIC_FILE.DATA_TYPE.GVCF_INDEX,
    ".vcf.gz.tbi": GENOMIC_FILE.DATA_TYPE.VARIANT_CALLS_INDEX,
    ".md5": COMMON.OTHER,
}


def filter_df_by_file_ext(df):
    """
    Only keep rows where file extension is one of those in
    FILE_EXT_FORMAT_MAP.keys
    """
    df[CONCEPT.GENOMIC_FILE.FILE_FORMAT] = df["Key"].apply(file_format)
    return df[df[CONCEPT.GENOMIC_FILE.FILE_FORMAT].notnull()]


source_data_url = "{{ download_url }}"

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
    return FILE_EXT_FORMAT_MAP.get(genomic_file_ext(x))


def data_type(x):
    """
    Get genomic file data type by looking up file format in DATA_TYPES.
    However, some types share formats, so then use the file extension itself
    to do the data type lookup.
    """
    return (
        DATA_TYPES.get(file_format(x)) or
        DATA_TYPES.get(genomic_file_ext(x))
    )


def fname(key):
    """
    Return just the filename portion of the key
    """
    return key.rsplit("/", 1)[-1]


operations = [
    row_map(out_col=CONCEPT.GENOMIC_FILE.ID, m=s3_url),
    row_map(
        out_col=CONCEPT.GENOMIC_FILE.URL_LIST, m=lambda row: [s3_url(row)]
    ),
    value_map(in_col="Key", out_col=CONCEPT.GENOMIC_FILE.FILE_NAME, m=fname),
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
        m=data_type,
    ),
]
