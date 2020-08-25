from creator.files.models import File, Version
from creator.events.models import Event
from creator.studies.factories import StudyFactory
from django.contrib.auth import get_user_model

User = get_user_model()

UPDATE_VERSION = """
mutation (
    $kfId:String!,
    $state: VersionState!,
    $description: String,
) {
    updateVersion(
        kfId: $kfId,
        description: $description
        state: $state
    ) {
        version { id kfId state description size }
    }
}
"""


def test_new_version_event(db, clients, upload_file, upload_version):
    """
    Test that new versions create events
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    resp = upload_file(study.kf_id, "manifest.txt", client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=file_id)
    user = User.objects.first()

    resp = upload_version("manifest.txt", file_id=file.kf_id, client=client)
    version = Version.objects.get(
        kf_id=resp.json()["data"]["createVersion"]["version"]["kfId"]
    )

    assert Event.objects.count() == 4
    assert Event.objects.filter(event_type="FV_CRE").count() == 2

    fv_cre = Event.objects.filter(event_type="FV_CRE").latest("created_at")
    assert fv_cre.user == user
    assert fv_cre.file == file
    assert fv_cre.version == version


def test_update_version_event(db, clients, upload_file, upload_version):
    """
    Test that updating versions create events
    """
    client = clients.get("Administrators")
    study = StudyFactory()
    resp = upload_file(study.kf_id, "manifest.txt", client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=file_id)
    version = file.versions.first()
    user = User.objects.first()

    variables = {"kfId": version.kf_id, "state": "PRC"}
    resp = client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_VERSION, "variables": variables},
    )

    assert Event.objects.count() == 4
    assert Event.objects.filter(event_type="FV_UPD").count() == 2

    fv_upd = Event.objects.filter(event_type="FV_UPD").first()
    assert fv_upd.user == user
    assert fv_upd.file == file
    assert fv_upd.version == version
