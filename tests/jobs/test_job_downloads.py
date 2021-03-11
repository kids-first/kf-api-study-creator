import pytest

from django.core import management
from django.http.response import HttpResponse

from creator.jobs.models import Job, JobLog


def test_job_download_url(clients, db, mocker):
    client = clients.get("Administrators")
    job = Job()
    job.save()
    assert Job.objects.count() == 1
    log = JobLog(job_id=job.pk)
    log.save()
    assert JobLog.objects.count() == 1

    mock_resp = mocker.patch("creator.jobs.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    query = "{allJobLogs { edges { node { downloadUrl } } } }"
    query_data = {"query": query.strip()}
    resp = client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allJobLogs" in resp.json()["data"]
    jobLog_json = resp.json()["data"]["allJobLogs"]["edges"][0]["node"]
    expect_url = (
        f"https://testserver/logs/{log.pk}"
    )
    assert jobLog_json["downloadUrl"] == expect_url


def test_job_download_url_develop(clients, db, mocker, settings):
    settings.DEVELOP = True
    management.call_command("setup_test_user")
    client = clients.get("Administrators")
    job = Job()
    job.save()
    assert Job.objects.count() == 1
    log = JobLog(job_id=job.pk)
    log.save()
    assert JobLog.objects.count() == 1

    mock_resp = mocker.patch("creator.jobs.views.HttpResponse")
    mock_resp.return_value = HttpResponse(open("tests/data/data.csv"))

    query = "{allJobLogs { edges { node { downloadUrl } } } } "
    query_data = {"query": query.strip()}
    resp = client.post(
        "/graphql", data=query_data, content_type="application/json"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "allJobLogs" in resp.json()["data"]
    jobLog_json = resp.json()["data"]["allJobLogs"]["edges"][0]["node"]
    expect_url = (
        f"http://testserver/logs/{log.pk}"
    )
    assert jobLog_json["downloadUrl"] == expect_url
