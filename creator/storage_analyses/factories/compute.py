import os

import humanize
import pandas
from pprint import pprint

from .data import FILE_EXT_FORMAT_MAP, DATA_TYPES


def only_complete_rows(df, required):
    """
    Filter out rows that are missing required values
    """
    missing_required = df[required].isnull().any(axis=1)
    df = df[~missing_required]
    return df


def drop_duplicates(df, required):
    """
    Drop duplicate rows
    """
    dups = df.duplicated(subset=required)
    df = df[~dups].reset_index(drop=True)
    return df


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
        status = "matched"
    elif merge == 'both' and (source_fn != fn):
        status = "moved"
    elif merge == "left_only":
        status = "missing"
    elif merge == "right_only":
        status = "unexpected"
    else:
        status = "unknown"
    return status


def file_url(row):
    """
    S3 url from bucket and key
    """
    bucket = row.get("Bucket")
    key = row.get("Key")

    if not (pandas.notnull(bucket) and pandas.notnull(key)):
        return None

    return f"s3://{bucket}/{key}"


def common_path(row):
    """
    Set file name/path of S3 object by extracting common path suffix between
    source file name/path and S3 Key
    """
    source = row["Source File Name"]
    dest = row["Key"]

    if pandas.isnull(dest) or pandas.isnull(source):
        return dest

    if dest.endswith(source):
        return source
    else:
        return os.path.basename(dest)


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
    required = ["Source File Name", "Hash", "Hash Algorithm", "Size"]
    required_inv = ["Bucket", "Key", "Hash", "Hash Algorithm", "Size"]

    upload_df = (
        pandas.concat(uploads)
        .sort_values("Created At", ascending=False)
    )
    # Remove rows that are missing req cols to do analysis
    upload_df = only_complete_rows(upload_df, required)
    inventory = only_complete_rows(inventory, required_inv)

    # Drop duplicates
    upload_df = drop_duplicates(upload_df, required)
    inventory = drop_duplicates(inventory, required_inv)

    # Rename columns
    upload_df = upload_df.rename(
        columns={
            col: f"Source {col}"
            for col in ["Hash", "Hash Algorithm", "Size"]
        }
    )

    # Join with s3 inventory
    file_audits = pandas.merge(
        upload_df, inventory,
        left_on="Source Hash", right_on="Hash",
        how="outer", indicator=True
    )

    file_audits.to_csv("file_audits_raw.csv", index=False)

    for c in ["Size", "Source Size"]:
        file_audits[c] = file_audits[c].apply(
            lambda x: int(float(x)) if x and pandas.notnull(x) else None
        )

    # Extract other necessary metadata
    file_audits["File Name"] = file_audits.apply(common_path, axis=1)
    file_audits["File Extension"] = file_audits.apply(file_ext, axis=1)
    file_audits["Data Type"] = file_audits.apply(data_type, axis=1)
    file_audits["Status"] = file_audits.apply(file_status, axis=1)
    file_audits["Url"] = file_audits.apply(file_url, axis=1)

    # Create dfs for analysis
    file_audits = file_audits[
        [
            "Status", "Url", "Bucket", "Key", "Size", "Hash", "Hash Algorithm",
            "File Name", "File Extension", "Data Type", "_merge"
        ] + [c for c in file_audits if c.startswith("Source")]
    ]

    matched = file_audits[file_audits["Status"] == "matched"]
    matched = drop_duplicates(
        matched, ["Source File Name", "File Name", "Hash"]
    )
    moved = file_audits[file_audits["Status"] == "moved"]
    moved = drop_duplicates(
        moved, ["Hash"]
    )
    missing = file_audits[file_audits["Status"] == "missing"]
    missing = drop_duplicates(
        missing, ["Source File Name", "Hash"]
    )
    unexpected = file_audits[file_audits["Status"] == "unexpected"]
    unexpected = drop_duplicates(
        unexpected, ["Url", "Hash"]
    )

    # TODO - We need to use originals here and add appropriate analysis cols
    uploads_df = pandas.concat([matched, moved, missing])
    inventory_df = pandas.concat([matched, moved, unexpected])

    stat_dfs = [
        ("matched", matched),
        ("missing", missing),
        ("moved", moved),
        ("unexpected", unexpected),
        ("inventory", inventory_df),
        ("uploads", uploads_df),
    ]

    # Compute storage analysis stats
    stats_dict = {"audit": {}}
    for key, df in stat_dfs:
        # Filter out invalid rows
        missing_required = df[["Hash", "Source Hash"]].isnull().all(axis=1)
        df = df[~missing_required]

        size_col = "Size" if key != "missing" else "Source Size"

        if df.empty:
            stats = {
                "total_count": 0,
                "total_size": 0,
                "count_by_size": 0,
                "count_by_ext": 0,
                "count_by_data_type": 0
            }
        else:
            # TODO - Remove later once original uploads and inventory dfs are
            # used and formatted for analysis
            if key == "inventory":
                total = inventory.shape[0]
            elif key == "uploads":
                total = upload_df.shape[0]
            else:
                total = df.shape[0]
            stats = {
                "total_count": total,
                "total_size": humanize.naturalsize(df[size_col].sum()),
                "count_by_size": file_count_by_size(df, size_col),
                "count_by_ext": df.groupby(["File Extension"]).size().to_dict(),
                "count_by_data_type": df.groupby(["Data Type"]).size().to_dict()
            }
        if key not in {"missing", "uploads"}:
            stats.update(
                {"total_buckets": df["Bucket"].nunique()}
            )
            stats.update(
                {"count_by_bucket": df.groupby(["Bucket"]).size().to_dict()}
            )
        if key in {"matched", "missing", "moved", "unexpected"}:
            stats_dict["audit"][key] = stats
        else:
            stats_dict[key] = stats

    return stats_dict, file_audits
