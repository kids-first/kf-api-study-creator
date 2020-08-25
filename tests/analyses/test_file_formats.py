from graphql_relay import from_global_id

from creator.studies.factories import StudyFactory
from creator.analyses.models import Analysis


def test_file_formats(db, clients, upload_file):
    """
    Test that each file format is interpretted identically for the same file
    contents.
    """

    client = clients.get("Administrators")
    study = StudyFactory()

    analyses = {
        "tsv": None,
        "csv": None,
        "xlsx": None,
        "xls": None,
    }

    for fmt in analyses.keys():
        resp = upload_file(
            study.kf_id,
            f"SD_ME0WME0W/FV_4DP2P2Y2_clinical.{fmt}",
            client=client,
        )

        analysis = resp.json()["data"]["createFile"]["file"]["versions"][
            "edges"
        ][0]["node"]["analysis"]

        _, analysis_id = from_global_id(analysis["id"])
        analysis = Analysis.objects.get(id=analysis_id)

        analyses[fmt] = analysis

    for attr in ["nrows", "ncols", "columns", "known_format"]:
        assert (
            getattr(analyses["csv"], attr)
            == getattr(analyses["tsv"], attr)
            == getattr(analyses["xlsx"], attr)
            == getattr(analyses["xls"], attr)
        )


def test_unknown_format(db, clients, upload_file):
    """
    """

    client = clients.get("Administrators")
    study = StudyFactory()

    resp = upload_file(
        study.kf_id, "SD_ME0WME0W/FV_4DP2P2Y2_clinical.txt", client=client
    )

    analysis = resp.json()["data"]["createFile"]["file"]["versions"]["edges"][
        0
    ]["node"]["analysis"]

    _, analysis_id = from_global_id(analysis["id"])
    analysis = Analysis.objects.get(id=analysis_id)

    assert analysis.known_format is False
    assert "not an understood" in analysis.error_message
