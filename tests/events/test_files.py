from creator.files.models import File
from creator.events.models import Event
from creator.studies.factories import StudyFactory
from django.contrib.auth import get_user_model

User = get_user_model()


UPDATE_FILE = """
mutation (
    $kfId:String!,
    $description: String!,
    $name: String!,
    $fileType: FileFileType!
) {
    updateFile(
        kfId: $kfId,
        name: $name,
        description:$description,
        fileType: $fileType
    ) {
        file { id kfId description name fileType }
    }
}
"""

DELETE_FILE = """
mutation ($kfId: String!) {
    deleteFile(kfId: $kfId) {
        success
    }
}
"""


def test_new_file_event(admin_client, db, upload_file):
    """
    Test that new file uploads create new events for both files and versions
    """
    assert Event.objects.count() == 0
    studies = StudyFactory.create_batch(1)
    study_id = studies[-1].kf_id
    resp = upload_file(study_id, "manifest.txt", admin_client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=file_id)
    version = file.versions.first()

    assert Event.objects.count() == 2
    assert Event.objects.filter(event_type="SF_CRE").count() == 1
    assert Event.objects.filter(event_type="FV_CRE").count() == 1
    user = User.objects.first()

    sf_cre = Event.objects.filter(event_type="SF_CRE").first()
    assert sf_cre.user == user
    assert sf_cre.file == file
    assert sf_cre.study == studies[0]

    fv_cre = Event.objects.filter(event_type="FV_CRE").first()
    assert fv_cre.user == user
    assert fv_cre.file == file
    assert fv_cre.version == version
    assert fv_cre.study == studies[0]


def test_file_updated_event(admin_client, db, upload_file):
    """
    Test that file updates create events
    """
    study_id = StudyFactory.create_batch(1)[0].kf_id
    resp = upload_file(study_id, "manifest.txt", admin_client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    assert Event.objects.count() == 2

    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_FILE, "variables": variables},
    )
    user = User.objects.first()
    assert Event.objects.count() == 3
    assert Event.objects.filter(event_type="SF_UPD").count() == 1
    assert Event.objects.filter(event_type="SF_UPD").first().user == user
    assert (
        Event.objects.filter(event_type="SF_UPD").first().study.kf_id
        == study_id
    )


def test_file_deleted_event(admin_client, db, upload_file):
    """
    Test that file deletions create events
    """
    study_id = StudyFactory.create_batch(1)[0].kf_id
    resp = upload_file(study_id, "manifest.txt", admin_client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    assert Event.objects.count() == 2

    variables = {"kfId": file_id}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": DELETE_FILE, "variables": variables},
    )
    user = User.objects.first()
    assert Event.objects.count() == 3
    assert Event.objects.filter(event_type="SF_DEL").count() == 1
    assert Event.objects.filter(event_type="SF_DEL").first().user == user
    assert (
        Event.objects.filter(event_type="SF_DEL").first().study.kf_id
        == study_id
    )