import os

import humanize
import pandas

from .data import FILE_EXT_FORMAT_MAP, DATA_TYPES


def filename_from_row(row):
    """
    Resolve file name from either the uploaded file or the file in S3
    """
    filenames = [row.get("File Name"), row.get("Source File Name")]
    for filename in filenames:
        if pandas.notnull(filename):
            return filename
    return None


def file_ext(row):
    """
    Try to get the right file extension from the filename
    Genomic files are tricky which is why we can't just use splitext
    """
    filename = filename_from_row(row)
    if not filename:
        return None

    matches = [
        file_ext
        for file_ext in FILE_EXT_FORMAT_MAP
        if filename.endswith(file_ext)
    ]
    if matches:
        file_ext = max(matches, key=len)
    else:
        file_ext = os.path.splitext(filename)[-1]

    return file_ext


def data_type(row):
    """
    Try to determine the data type of the file by inspecting the extension
    """
    filename = filename_from_row(row)
    if not filename:
        return None

    ext = file_ext(row)
    if 'tbi' in ext:
        data_type = DATA_TYPES.get(ext)
    else:
        data_type = DATA_TYPES.get(FILE_EXT_FORMAT_MAP.get(ext))

    if not data_type:
        data_type = "Other"

    return data_type


def file_status(row):
    """
    Determine the status of the file uploaded to cloud storage
    """
    source_fn = row["Source File Name"]
    fn = row["File Name"]
    merge = row["_merge"]

    if merge == 'both' and (source_fn == fn):
        status = "files_matched"
    elif merge == 'both' and (source_fn != fn):
        status = "files_differ"
    elif merge == "left_only":
        status = "files_missing"
    elif merge == "right_only":
        status = "inventory_only"
    else:
        status = "unknown"
    return status


def file_count_by_size(df, col):
    """
    Count files that are greater than a certain size
    Size bins are equally distributed across sizes in data
    """
    return {
        humanize.naturalsize(invt.left): count
        for invt, count in pandas.cut(df[col], bins=10)
        .value_counts().to_dict().items()
    }


def compute_storage_analysis(uploads, inventory):
    """
    Analyze a set of file upload manifests and an S3 inventory and produce
    a numerical summary along with a file audit table which lists every file
    analyzed
    """
    # Aggregate upload manifests
    # resolve duplicate file uploads by taking the latest one
    upload_df = (
        pandas.concat(uploads)
        .sort_values("Created At", ascending=False)
        .drop_duplicates("Hash")
        .reset_index(drop=True)
    ).rename(
        columns={
            col: f"Source {col}"
            for col in ["Hash Algorithm", "Size"]
        }
    )
    # Join with s3 inventory
    inventory["File Name"] = inventory["Key"].apply(
        lambda key: key.split("/")[-1]
    )
    file_audits = pandas.merge(
        upload_df, inventory, on="Hash", how="outer", indicator=True)

    # Extract file extension and data types
    file_audits["File Extension"] = file_audits.apply(file_ext, axis=1)
    file_audits["Data Type"] = file_audits.apply(data_type, axis=1)
    file_audits["Status"] = file_audits.apply(file_status, axis=1)

    # Create dfs for analysis
    file_audits = file_audits[
        [
            "Status", "Bucket", "Key", "Size", "Hash", "Hash Algorithm",
            "File Name", "File Extension", "Data Type", "_merge"
        ] + [c for c in file_audits if c.startswith("Source")]
    ]

    files_matched = file_audits[file_audits["Status"] == "files_matched"]
    files_missing = file_audits[file_audits["Status"] == "files_missing"]
    files_differ = file_audits[file_audits["Status"] == "files_differ"]
    inventory_only = file_audits[file_audits["Status"] == "inventory_only"]
    uploads_df = pandas.concat([files_matched, files_missing])
    inventory_df = pandas.concat([files_matched, inventory_only])

    stat_dfs = [
        ("files_matched", files_matched),
        ("files_missing", files_missing),
        ("files_differ", files_differ),
        ("inventory", inventory_df),
        ("uploads", uploads_df),
    ]

    # Compute storage analysis stats
    stats_dict = {"audit": {}}
    for key, df in stat_dfs:
        size_col = "Size" if key != "files_missing" else "Source Size"
        stats = {
            "total_count": int(df["Hash"].count()),
            "total_size": humanize.naturalsize(df[size_col].sum()),
            "count_by_size": file_count_by_size(df, size_col),
            "count_by_ext": df.groupby(["File Extension"]).size().to_dict(),
            "count_by_data_type": df.groupby(["Data Type"]).size().to_dict()
        }
        if key not in {"files_missing", "uploads"}:
            stats.update(
                {"total_buckets": df["Bucket"].nunique()}
            )
            stats.update(
                {"count_by_bucket": df.groupby(["Bucket"]).size().to_dict()}
            )
        if key.startswith("files"):
            stats_dict["audit"][key] = stats
        else:
            stats_dict[key] = stats

    return stats_dict, file_audits
