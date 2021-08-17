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
    $fileType: FileType!
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


def test_new_file_event(clients, db, upload_file):
    """
    Test that new file uploads create new events for both files and versions
    """
    client = clients.get("Administrators")
    assert Event.objects.count() == 0
    studies = StudyFactory.create_batch(1, files=0)
    study_id = studies[-1].kf_id
    resp = upload_file(study_id, "manifest.txt", client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=file_id)
    version = file.versions.first()

    assert Event.objects.count() == 3
    assert Event.objects.filter(event_type="SF_CRE").count() == 1
    assert Event.objects.filter(event_type="FV_CRE").count() == 1
    assert Event.objects.filter(event_type="FV_UPD").count() == 1
    user = User.objects.filter(groups__name="Administrators").first()

    sf_cre = Event.objects.filter(event_type="SF_CRE").first()
    assert sf_cre.user == user
    assert sf_cre.file == file
    assert sf_cre.study == studies[0]

    fv_cre = Event.objects.filter(event_type="FV_CRE").first()
    assert fv_cre.user == user
    assert fv_cre.file is None
    assert fv_cre.version == version
    assert fv_cre.study == studies[0]

    fv_upd = Event.objects.filter(event_type="FV_UPD").first()
    assert fv_upd.user == user
    assert fv_upd.file == file
    assert fv_upd.version == version
    assert fv_upd.study == studies[0]


def test_file_updated_event(db, clients, upload_file):
    """
    Test that file updates create events
    """
    client = clients.get("Administrators")
    study = StudyFactory(files=0)
    resp = upload_file(study.kf_id, "manifest.txt", client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    assert Event.objects.count() == 3

    variables = {
        "kfId": file_id,
        "name": "New name",
        "description": "New description",
        "fileType": "FAM",
    }
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_FILE, "variables": variables},
    )
    user = User.objects.first()
    assert Event.objects.count() == 4
    assert Event.objects.filter(event_type="SF_UPD").count() == 1
    assert Event.objects.filter(event_type="SF_UPD").first().user == user
    assert (
        Event.objects.filter(event_type="SF_UPD").first().study.kf_id
        == study.kf_id
    )


def test_file_deleted_event(db, clients, upload_file):
    """
    Test that file deletions create events
    """
    client = clients.get("Administrators")
    study = StudyFactory(files=0)
    resp = upload_file(study.kf_id, "manifest.txt", client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    assert Event.objects.count() == 3

    variables = {"kfId": file_id}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": DELETE_FILE, "variables": variables},
    )
    user = User.objects.first()
    assert Event.objects.count() == 4
    assert Event.objects.filter(event_type="SF_DEL").count() == 1
    assert Event.objects.filter(event_type="SF_DEL").first().user == user
    assert (
        Event.objects.filter(event_type="SF_DEL").first().study.kf_id
        == study.kf_id
    )
