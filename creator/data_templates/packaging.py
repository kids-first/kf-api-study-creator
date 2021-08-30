from typing import Union, List, Optional
import os
from zipfile import ZipFile
from io import BytesIO
from pprint import pformat

import pandas

from creator.studies.models import Study
from creator.data_templates.models import TemplateVersion

MAX_SHEET_NAME_LEN = 31

PACKAGE_INFO = """
    The Fields file describes all of the fields or columns in the template
    (name, data type, required or not, etc.) while the blank Template file
    is what data submitters will fill out and then submit to their
    organization for ingestion.
    """


def make_sheet_name(template_name: str, type_: str):
    """
    Helper to create a Excel sheet name from the template name and it's type
    (e.g. Fields or Template)

    Create a sheet_name by putting together the template name and type. If
    its > the max char limit for sheet names, truncate the template name
    until the sheet_name has a valid length
    """
    # Truncates template name to avoid Excel writer exception
    suffix = f" - {type_}"
    return template_name[: (MAX_SHEET_NAME_LEN - len(suffix))] + suffix


def templates_to_excel_workbook(
    template_versions: List[TemplateVersion],
    filepath_or_buffer: Optional[Union[str, BytesIO]] = None,
):
    """
    Write templates to disk as an Excel workbook

    First add a sheet for the table of contents, listing each template's name,
    description and associated sheets in the workbook.

    Then add 2 sheets for each TemplateVersion. One for the blank template
    and one for the template's field definitions

    Style sheets: Center column names, wrap text in all cells, vertically
    center text, fixed col width, color header row
    """
    # Set default
    if not filepath_or_buffer:
        filepath_or_buffer = os.path.join(os.getcwd(), "template_package.xlsx")

    # Ensure we have correct file ext
    if isinstance(filepath_or_buffer, str):
        output_dir, filename = os.path.split(filepath_or_buffer)
        filename = os.path.splitext(filename)[0] + ".xlsx"
        filepath_or_buffer = os.path.join(output_dir, filename)

    writer = pandas.ExcelWriter(filepath_or_buffer, engine="xlsxwriter")
    toc = []
    sheets = {}
    for tv in template_versions:
        dfs = [
            (tv.field_definitions_dataframe, "Fields"),
            (tv.template_dataframe, "Template"),
        ]
        toc_item = {
            "Template Name": tv.data_template.name,
            "Template Description": tv.data_template.description,
            "Sheets": [],
            "Info": PACKAGE_INFO,
        }
        for df, type_ in dfs:
            sheet_name = make_sheet_name(tv.data_template.name, type_)
            sheets[sheet_name] = df
            toc_item["Sheets"].append(sheet_name)

        # Add toc entry
        toc.append(toc_item)

    # Prevent Pandas to_excel from styling header row with its defaults
    kwargs = {
        "startrow": 1,
        "header": False,
        "index": False,
    }
    # Write table of contents as first sheet
    toc = pandas.DataFrame(toc)
    toc["Sheets"] = toc["Sheets"].apply(
        lambda sheets: "\n".join(s for s in sheets)
    )
    toc.to_excel(writer, sheet_name="Table of Contents", **kwargs)

    # Write template, field definitions sheets to workbook
    for sheet_name, df in sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, **kwargs)

    sheets["Table of Contents"] = toc

    # Apply styles to workbook
    workbook = writer.book
    header_format = workbook.add_format(
        {
            "bold": True,
            "text_wrap": True,
            "align": "center",
            "valign": "vcenter",
            "font_size": 12,
            "bg_color": "#f4f4f4",
            "bottom": 1,
        }
    )
    first_col_format = workbook.add_format({"bold": True, "valign": "vcenter"})
    default_format = workbook.add_format(
        {"text_wrap": True, "valign": "vcenter"}
    )
    for sheet_name, sheet in writer.sheets.items():
        df = sheets[sheet_name]

        # Style first col
        # Unfortunately there is no way to autofit col so just pick something
        sheet.set_column(0, 0, 30, cell_format=first_col_format)
        # Default formatting
        sheet.set_column(1, df.shape[1] - 1, 30, cell_format=default_format)
        # Freeze first row
        sheet.freeze_panes(1, 0)

        # Style header row
        for col_num, value in enumerate(df.columns.values):
            sheet.write(0, col_num, value, header_format)

    writer.save()

    return filepath_or_buffer


def templates_to_archive(
    template_versions: List[TemplateVersion],
    filepath_or_buffer: Optional[Union[str, BytesIO]] = None,
):
    """
    Write templates to disk as TSVs in a zip archive

    Include a table of contents file detailing the templates in this archive
    Then write 2 tsv files for each TemplateVersion. One for the
    blank template and one for the template's field definitions
    """
    # Set defaults
    archive_name = "template_package"
    if not filepath_or_buffer:
        filepath_or_buffer = os.path.join(os.getcwd(), archive_name + ".zip")

    # Ensure we have correct file ext
    # If user provided the filepath, use its dirname as the archive name
    if isinstance(filepath_or_buffer, str):
        output_dir, filename = os.path.split(filepath_or_buffer)
        archive_name = os.path.splitext(filename)[0]
        filename = archive_name + ".zip"
        filepath_or_buffer = os.path.join(output_dir, filename)

    # Write templates, field definitions, and a table of contents to zip
    with ZipFile(filepath_or_buffer, "w") as zip_archive:
        toc = []
        contents = []
        for tv in template_versions:
            template_name = "-".join(tv.data_template.name.split(" ")).lower()
            files = [
                (f"{template_name}-template.tsv", tv.template_dataframe),
                (
                    f"{template_name}-fields.tsv",
                    tv.field_definitions_dataframe,
                ),
            ]
            contents.extend(files)
            toc.append(
                {
                    "Template Name": tv.data_template.name,
                    "Template Description": tv.data_template.description,
                    "Files": "\n".join([fname for fname, _ in files]),
                    "Info": PACKAGE_INFO,
                }
            )
        contents.append(("table_of_contents.tsv", pandas.DataFrame(toc)))
        for fn, df in contents:
            with zip_archive.open(f"{archive_name}/{fn}", "w") as file:
                stream = BytesIO()
                df.to_csv(stream, sep="\t", index=False)
                file.write(stream.getvalue())
                stream.close()

    return filepath_or_buffer


def template_package(
    study_kf_id: str = None,
    filepath_or_buffer: Optional[Union[str, BytesIO]] = None,
    template_version_ids: Optional[List[str]] = None,
    excel_workbook: bool = True,
):
    """
    Fetch a set of templates and package into an Excel workbook or zip file
    Optionally filter templates by study or a set of template_version IDs

    Used when user requests to download templates
    """
    if study_kf_id is None and template_version_ids is None:
        # No input provided, error
        raise ValueError("No input provided")

    if study_kf_id:
        study = Study.objects.get(pk=study_kf_id)
        query_manager = study.template_versions
    else:
        query_manager = TemplateVersion.objects

    # Filter down templates
    if template_version_ids:
        template_versions = query_manager.filter(
            pk__in=template_version_ids
        ).all()

        # One or more template versions did not exist
        if {tv.pk for tv in template_versions} != set(template_version_ids):
            raise TemplateVersion.DoesNotExist(
                "One or more template versions does not exist"
            )

    # All study templates
    else:
        template_versions = query_manager.all()

        if not template_versions:
            raise TemplateVersion.DoesNotExist(
                f"No templates exist for study {study_kf_id}"
            )

    # Check for duplicate template names
    # Duplicate names are bad bc we use them for template file names/Excel
    # sheet names when packaging templates
    count = len(template_versions)
    names = {tv.data_template.name for tv in template_versions}
    if len(names) != count:
        raise ValueError(
            f"Cannot package templates with duplicate names: {pformat(names)}"
        )

    if not filepath_or_buffer:
        filename = (
            f"{study_kf_id}_templates" if study_kf_id else "template_package"
        )
        filepath_or_buffer = os.path.join(os.getcwd(), filename)

    if excel_workbook:
        path_or_buf = templates_to_excel_workbook(
            template_versions,
            filepath_or_buffer=filepath_or_buffer,
        )
    else:
        path_or_buf = templates_to_archive(
            template_versions,
            filepath_or_buffer=filepath_or_buffer,
        )

    return path_or_buf
